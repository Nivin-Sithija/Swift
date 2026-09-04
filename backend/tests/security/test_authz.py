"""Access control: authentication, role separation, and object ownership.

These are the tests that decide whether one customer can read another customer's
banking complaint. They drive the real ASGI stack rather than calling route
functions, because a dependency that is wired to the wrong route is exactly the
kind of defect a direct call cannot see.
"""

import uuid

import jwt
import pytest

from app.core.security import create_access_token

pytestmark = pytest.mark.security


STAFF_ONLY = [
    ("get", "/dashboard/metrics"),
    ("post", "/tickets/{ticket}/notes"),
    ("put", "/tickets/{ticket}/status"),
    ("put", "/tickets/{ticket}/assignment"),
    ("post", "/tickets/{ticket}/escalate"),
]

ADMIN_ONLY = [
    ("get", "/admin/dashboard"),
    ("get", "/admin/users"),
    ("get", "/admin/queues"),
    ("post", "/admin/queues"),
    ("get", "/admin/audit-logs"),
    ("get", "/admin/settings"),
    ("patch", "/admin/settings"),
]


async def _call(client, method: str, path: str, headers: dict[str, str] | None = None):
    return await client.request(method.upper(), path, headers=headers or {}, json={})


# --- authentication ---------------------------------------------------------


@pytest.mark.parametrize("path", ["/users/me", "/tickets", "/dashboard/metrics", "/admin/users"])
async def test_protected_routes_reject_anonymous_callers(client, path):
    assert (await client.get(path)).status_code in (401, 403)


async def test_expired_token_is_rejected(client, customer):
    expired = jwt.encode(
        {
            "sub": str(customer.id),
            "role": customer.role.value,
            "type": "access",
            "exp": 1_600_000_000,
        },
        "development-only-change-me-at-least-32-characters",
        algorithm="HS256",
    )
    response = await client.get("/users/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


async def test_token_signed_with_a_different_key_is_rejected(client, customer):
    """The signature must be what grants access, not the claims inside it."""
    forged = jwt.encode(
        {"sub": str(customer.id), "role": "administrator", "type": "access", "exp": 9_999_999_999},
        "an-attacker-controlled-key-of-sufficient-length",
        algorithm="HS256",
    )
    response = await client.get("/users/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


async def test_alg_none_token_is_rejected(client, customer):
    """CVE-class check: an unsigned token must never authenticate."""
    unsigned = jwt.encode(
        {"sub": str(customer.id), "role": "administrator", "type": "access"},
        key="",
        algorithm="none",
    )
    response = await client.get("/users/me", headers={"Authorization": f"Bearer {unsigned}"})
    assert response.status_code == 401


async def test_refresh_token_cannot_be_used_as_an_access_token(client, customer, db):
    """Token type confusion: the two token classes must not be interchangeable."""
    from app.core.security import new_refresh_token

    raw, _ = new_refresh_token()
    response = await client.get("/users/me", headers={"Authorization": f"Bearer {raw}"})
    assert response.status_code == 401


async def test_deactivated_account_loses_access_immediately(client, customer, db):
    headers = {"Authorization": f"Bearer {create_access_token(customer.id, 'customer')}"}
    assert (await client.get("/users/me", headers=headers)).status_code == 200

    customer.is_active = False
    await db.commit()

    # The token is still cryptographically valid; the account check is what must deny it.
    assert (await client.get("/users/me", headers=headers)).status_code == 401


# --- role separation --------------------------------------------------------


@pytest.mark.parametrize("method,path", STAFF_ONLY)
async def test_customer_cannot_reach_staff_routes(client, customer, new_ticket, auth_headers, method, path):
    ticket = await new_ticket(customer)
    response = await _call(client, method, path.format(ticket=ticket), auth_headers(customer))
    assert response.status_code == 403, f"{method.upper()} {path} allowed a customer"


@pytest.mark.parametrize("method,path", ADMIN_ONLY)
async def test_agent_cannot_reach_administrator_routes(client, agent, auth_headers, method, path):
    response = await _call(client, method, path, auth_headers(agent))
    assert response.status_code == 403, f"{method.upper()} {path} allowed an agent"


async def test_role_claim_in_token_does_not_override_stored_role(client, customer, auth_headers):
    """Privilege escalation: the database role must win over the token's claim."""
    escalated = create_access_token(customer.id, "administrator")
    response = await client.get("/admin/users", headers={"Authorization": f"Bearer {escalated}"})
    assert response.status_code == 403


async def test_agent_self_promotion_is_blocked(client, agent, auth_headers):
    response = await client.patch(
        f"/admin/users/{agent.id}", json={"role": "administrator"}, headers=auth_headers(agent)
    )
    assert response.status_code == 403


# --- object ownership (IDOR) ------------------------------------------------


async def test_customer_cannot_read_another_customers_ticket(
    client, customer, other_customer, new_ticket, auth_headers
):
    ticket = await new_ticket(customer)
    response = await client.get(f"/tickets/{ticket}", headers=auth_headers(other_customer))
    assert response.status_code in (403, 404), "one customer read another's ticket"


async def test_ticket_list_is_scoped_to_the_caller(
    client, customer, other_customer, new_ticket, auth_headers
):
    await new_ticket(customer, "My own ticket")
    await new_ticket(other_customer, "Their ticket")

    body = (await client.get("/tickets", headers=auth_headers(customer))).json()
    assert body["total"] == 1
    assert body["items"][0]["subject"] == "My own ticket"


async def test_unknown_ticket_reference_is_not_a_server_error(client, customer, auth_headers):
    response = await client.get("/tickets/SW-2026-999999", headers=auth_headers(customer))
    assert response.status_code == 404


async def test_attachment_of_another_customer_cannot_be_downloaded(
    client, customer, other_customer, new_ticket, auth_headers
):
    ticket = await new_ticket(customer)
    upload = await client.post(
        f"/tickets/{ticket}/attachments",
        files={"file": ("proof.png", b"\x89PNG\r\n\x1a\n" + b"0" * 64, "image/png")},
        headers=auth_headers(customer),
    )
    assert upload.status_code == 201, upload.text
    attachment_id = upload.json()["id"]

    response = await client.get(
        f"/attachments/{attachment_id}/download", headers=auth_headers(other_customer)
    )
    assert response.status_code in (403, 404), "attachment leaked across customers"


async def test_attachment_owner_can_download_their_own(
    client, customer, new_ticket, auth_headers
):
    """Guards the negative test above: proves the route is reachable and 200s for the owner,
    so a 404 for the other customer is a denial and not a mis-typed URL."""
    ticket = await new_ticket(customer)
    upload = await client.post(
        f"/tickets/{ticket}/attachments",
        files={"file": ("proof.png", b"\x89PNG\r\n\x1a\n" + b"0" * 64, "image/png")},
        headers=auth_headers(customer),
    )
    attachment_id = upload.json()["id"]
    response = await client.get(
        f"/attachments/{attachment_id}/download", headers=auth_headers(customer)
    )
    assert response.status_code == 200


async def test_random_attachment_id_returns_not_found(client, customer, auth_headers):
    response = await client.get(f"/attachments/{uuid.uuid4()}/download", headers=auth_headers(customer))
    assert response.status_code == 404
