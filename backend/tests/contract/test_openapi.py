"""API contract conformance.

Two different questions live here:

  * Drift — `docs/api/api_contract.yaml` is hand-written and committed as the
    published contract. Nothing keeps it in step with the routes, so it is checked
    against the live app rather than trusted.
  * Property testing — Schemathesis generates inputs from the app's own schema and
    asserts the server never contradicts it: no unhandled 500, no undeclared status
    code, no response that violates its own declared shape.
"""

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.contract

REPO = Path(__file__).resolve().parents[3]
CONTRACT = REPO / "docs" / "api" / "api_contract.yaml"
VERBS = {"get", "post", "put", "patch", "delete"}


def app_paths(app) -> set[tuple[str, str]]:
    """(method, path) pairs the running application actually serves."""
    return {
        (method.lower(), path)
        for path, operations in app.openapi()["paths"].items()
        for method in operations
        if method.lower() in VERBS
    }


def documented_paths() -> set[tuple[str, str]]:
    document = yaml.safe_load(CONTRACT.read_text())
    return {
        (method.lower(), f"/api/v1{path}")
        for path, operations in document["paths"].items()
        for method in operations
        if method.lower() in VERBS
    }


# --- the published contract -------------------------------------------------


def test_the_published_contract_is_valid_openapi_3():
    document = yaml.safe_load(CONTRACT.read_text())
    assert document["openapi"].startswith("3.")
    assert document["paths"]


def test_no_documented_endpoint_is_missing_from_the_app(app):
    """A contract promising a route the server does not serve breaks integrators."""
    missing = documented_paths() - app_paths(app)
    assert not missing, f"documented but not implemented: {sorted(missing)}"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "docs/api/api_contract.yaml predates the admin surface: 9 /admin/* routes plus "
        "/auth/register are served but undocumented."
    ),
)
def test_contract_covers_the_routes_it_claims_to_cover(app):
    """Drift report. The contract scopes RAG out explicitly, so that route is
    allowed to be absent; everything else it omits is genuine drift."""
    out_of_scope = {("post", "/api/v1/tickets/{ticket_id}/assistance")}
    undocumented = app_paths(app) - documented_paths() - out_of_scope
    assert not undocumented, (
        f"{len(undocumented)} routes served but not in docs/api/api_contract.yaml: "
        f"{sorted(path for _, path in undocumented)}"
    )


def test_contract_drift_has_not_grown(app):
    """Ratchet: the known drift is 10 routes. New undocumented routes fail here."""
    out_of_scope = {("post", "/api/v1/tickets/{ticket_id}/assistance")}
    undocumented = app_paths(app) - documented_paths() - out_of_scope
    assert len(undocumented) <= 10, (
        f"contract drift grew to {len(undocumented)}: {sorted(undocumented)}"
    )


# --- schema self-consistency ------------------------------------------------


def test_security_scheme_is_declared(app):
    assert "securitySchemes" in app.openapi().get("components", {}), (
        "no security scheme in the generated OpenAPI document"
    )


async def test_openapi_document_is_reachable_over_http(client):
    response = await client.get("http://test/openapi.json")
    assert response.status_code == 200
    assert response.json()["openapi"].startswith("3.")


def test_error_shape_is_consistent_across_failures(app):
    """Every declared 4xx/5xx should describe a body, so clients can parse errors
    the same way regardless of which route produced them."""
    schema = app.openapi()
    silent = [
        f"{method.upper()} {path} -> {code}"
        for path, operations in schema["paths"].items()
        for method, operation in operations.items()
        if method.lower() in VERBS
        for code, body in operation.get("responses", {}).items()
        if code.startswith(("4", "5")) and "content" not in body
    ]
    # Recorded rather than enforced: FastAPI's auto-added 422 always has content,
    # so anything here is a hand-written response missing a schema.
    assert len(silent) < 40, f"{len(silent)} error responses declare no body: {silent[:10]}"


# --- Schemathesis property tests --------------------------------------------

schemathesis = pytest.importorskip("schemathesis")


@pytest.fixture(scope="module")
def api_schema():
    """Load the schema from the app object directly.

    Building it from the ASGI app rather than a URL keeps the property tests
    offline and independent of a running server.
    """
    from app.main import app as fastapi_app

    return schemathesis.openapi.from_dict(fastapi_app.openapi())


@pytest.mark.slow
def test_schema_is_well_formed(api_schema):
    """Schemathesis refuses to build operations from an invalid schema, so simply
    enumerating them is a real check that the generated document is coherent."""
    operations = list(api_schema.get_all_operations())
    assert operations, "no operations parsed from the OpenAPI document"

    errors = [item for item in operations if not hasattr(item, "ok")]
    assert not errors, errors


@pytest.mark.slow
def test_every_operation_has_a_unique_operation_id(app):
    """Duplicate operationIds silently break generated client SDKs."""
    seen: dict[str, str] = {}
    duplicates = []
    for path, operations in app.openapi()["paths"].items():
        for method, operation in operations.items():
            if method.lower() not in VERBS:
                continue
            identifier = operation.get("operationId")
            if identifier is None:
                continue
            if identifier in seen:
                duplicates.append(f"{identifier}: {seen[identifier]} and {method.upper()} {path}")
            seen[identifier] = f"{method.upper()} {path}"
    assert not duplicates, duplicates
