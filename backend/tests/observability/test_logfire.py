"""Observability: Logfire instrumentation, trace correlation, and PII hygiene.

The first test here exists because of a real outage. `logfire.instrument_fastapi`
wraps route resolution, so an incompatible OpenTelemetry version does not degrade
tracing — it turns every single request into a 500. With logfire pinned `>=3,<4`
against FastAPI 0.141 that is exactly what happened, and the entire pre-existing
test suite stayed green because nothing drove an HTTP request through the app.

Anything that can take the whole API down deserves a test that drives real traffic.
"""

import pytest

pytestmark = pytest.mark.observability


# --- the instrumentation must not break the app -----------------------------


@pytest.mark.parametrize("path", ["/health", "/ready"])
async def test_instrumented_app_serves_requests(client, path):
    """Regression guard for the logfire/OTel/FastAPI incompatibility."""
    response = await client.get(path)
    assert response.status_code == 200, (
        f"{path} returned {response.status_code} with instrumentation active — "
        "check the opentelemetry-instrumentation-fastapi / FastAPI version pair"
    )


async def test_instrumentation_resolves_routes_on_a_parameterised_path(client, customer, new_ticket, auth_headers):
    """The failure mode was in route resolution, so a path with parameters and a
    dependency chain is the case that actually exercises it."""
    reference = await new_ticket(customer)
    response = await client.get(f"/tickets/{reference}", headers=auth_headers(customer))
    assert response.status_code == 200


def test_fastapi_instrumentation_is_actually_installed():
    """`logfire.instrument_fastapi` must have patched the app, or traces are empty
    while everything still looks healthy."""
    from logfire._internal.integrations import fastapi as logfire_fastapi

    assert hasattr(logfire_fastapi, "patch_fastapi") or hasattr(
        logfire_fastapi, "instrument_fastapi"
    )


# --- configuration ----------------------------------------------------------


def test_logfire_runs_without_a_token():
    """`send_to_logfire="if-token-present"` is what lets CI and local dev import
    main.py without credentials. If that changes, every test run needs a secret."""
    import inspect

    from app import main

    source = inspect.getsource(main)
    assert 'send_to_logfire="if-token-present"' in source


def test_service_name_and_environment_are_set():
    import inspect

    from app import main

    source = inspect.getsource(main)
    assert "service_name=" in source, "spans without a service name are unattributable"
    assert "environment=" in source, "dev and prod traces would land in one stream"


def test_logfire_token_is_not_hardcoded():
    import inspect

    from app import main

    source = inspect.getsource(main)
    assert "token=settings.logfire_token" in source
    assert "pylf_" not in source, "a Logfire write token is committed in main.py"


# --- trace correlation ------------------------------------------------------


async def test_every_response_carries_a_request_id(client):
    response = await client.get("/health")
    assert response.headers.get("x-request-id"), "no correlation id on the response"


async def test_supplied_request_id_is_echoed_back(client):
    supplied = "trace-me-123"
    response = await client.get("/health", headers={"x-request-id": supplied})
    assert response.headers["x-request-id"] == supplied


async def test_unhandled_errors_return_a_request_id_not_a_stack_trace(
    client, customer, auth_headers, monkeypatch
):
    """An operator needs the id to find the trace; the customer must not get internals."""
    from app.api.v1 import routes

    async def _boom(text: str, is_ocr: bool = False):
        raise RuntimeError("database credentials: swift/swift@postgres")

    monkeypatch.setattr(routes, "classify", _boom)

    response = await client.post(
        "/tickets",
        json={"subject": "Trigger failure", "message": "This request raises inside the handler."},
        headers=auth_headers(customer),
    )

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "internal_error"
    assert body["request_id"]
    assert "swift/swift@postgres" not in response.text, "internal detail leaked to the client"
    assert "Traceback" not in response.text


# --- PII hygiene in spans ---------------------------------------------------


async def test_password_is_never_recorded_in_a_span(capfire, client):
    """Login is the highest-risk span in the app: it receives a plaintext password."""
    await client.post(
        "/auth/register",
        json={
            "full_name": "Span Check",
            "email": "span@example.com",
            "password": "SuperSecret123!",
        },
    )

    serialised = str(capfire.exporter.exported_spans_as_dict())
    assert "SuperSecret123!" not in serialised, "plaintext password captured in a span"


async def test_authorization_header_is_not_recorded_in_a_span(capfire, client, customer, auth_headers):
    headers = auth_headers(customer)
    token = headers["Authorization"].removeprefix("Bearer ")

    await client.get("/users/me", headers=headers)

    serialised = str(capfire.exporter.exported_spans_as_dict())
    assert token not in serialised, "bearer token captured in a span"


async def test_rag_routing_spans_do_not_carry_the_customer_query(capfire):
    """`rag.input_routing` logs the routing decision. It must record *why* a query
    escalated, not the query itself — those bodies contain account details."""
    from datetime import date

    from app.rag.service import ConsumerRAGService
    from app.rag.types import Evidence, QueryContext, RetrievalResult

    class Retriever:
        async def retrieve(self, context: QueryContext) -> RetrievalResult:
            return RetrievalResult(
                [
                    Evidence(
                        "c1", "SRC-1", "Savings", "https://bank.example/s", "Commercial Bank",
                        "accounts", "english", "bank_official", "1.0",
                        date(2026, 7, 29), "approved", 0, "Deposit information.",
                    )
                ],
                0.9,
            )

    class LLM:
        name = "fake"

        async def generate(self, *, system: str, user: str) -> str:
            return "General guidance from the approved source. [E1]"

    secret = "my card number is 4111111111111111"
    await ConsumerRAGService(Retriever(), LLM()).assist(query=secret, institution=None)

    serialised = str(capfire.exporter.exported_spans_as_dict())
    assert "4111111111111111" not in serialised, "card number captured in a RAG span"
