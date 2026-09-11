"""Rate limiting and abuse resistance.

The application has no rate limiting of any kind — no middleware, no dependency,
no Redis token bucket, despite Redis already being a running dependency. Every
test here is therefore marked `xfail(strict=True)`: it encodes the behaviour the
endpoint should have, stays green while the gap is known, and starts failing the
moment someone implements a limiter, which is the signal to delete the marker.

Priority order if only some get implemented:
  1. /auth/login          — unthrottled credential brute force
  2. /tickets/{id}/assistance — every call is a paid Groq/Gemini generation
  3. /auth/register       — free account creation
  4. /tickets/{id}/attachments — 10 MB per request, unbounded
"""

import pytest

pytestmark = pytest.mark.security

GAP = "No rate limiting implemented; see backend/app/main.py (no limiter middleware)."


@pytest.mark.xfail(strict=True, reason=GAP)
async def test_repeated_failed_logins_are_throttled(client, customer):
    """A password guesser must be slowed down before it exhausts the keyspace."""
    statuses = []
    for _ in range(25):
        response = await client.post(
            "/auth/login", json={"email": customer.email, "password": "WrongPassword1!"}
        )
        statuses.append(response.status_code)

    assert 429 in statuses, f"25 failed logins all returned {set(statuses)} — no lockout"


@pytest.mark.xfail(strict=True, reason=GAP)
async def test_account_is_locked_after_sustained_brute_force(client, customer):
    """After lockout the *correct* password must also be refused, or the limiter
    only delays the attacker rather than stopping the attack."""
    for _ in range(25):
        await client.post(
            "/auth/login", json={"email": customer.email, "password": "WrongPassword1!"}
        )

    response = await client.post(
        "/auth/login", json={"email": customer.email, "password": "CorrectHorse9!"}
    )
    assert response.status_code == 429


@pytest.mark.xfail(strict=True, reason=GAP)
async def test_registration_is_rate_limited(client):
    statuses = []
    for index in range(25):
        response = await client.post(
            "/auth/register",
            json={
                "full_name": "Flood Bot",
                "email": f"flood-{index}@example.com",
                "password": "CorrectHorse9!",
            },
        )
        statuses.append(response.status_code)

    assert 429 in statuses, "25 accounts created back-to-back with no throttle"


@pytest.mark.xfail(strict=True, reason=GAP)
async def test_ticket_creation_is_rate_limited(client, customer, auth_headers):
    """Each ticket triggers a classification call; unbounded creation is a cost attack."""
    statuses = []
    for index in range(30):
        response = await client.post(
            "/tickets",
            json={
                "subject": f"Flood ticket {index}",
                "message": "This message exists only to occupy the queue and burn inference.",
            },
            headers=auth_headers(customer),
        )
        statuses.append(response.status_code)

    assert 429 in statuses


@pytest.mark.xfail(strict=True, reason=GAP)
async def test_attachment_upload_is_rate_limited(client, customer, new_ticket, auth_headers):
    """max_upload_bytes caps one request at 10 MB but nothing caps requests per minute,
    so a customer can write unbounded data to the attachment volume."""
    ticket = await new_ticket(customer)
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 2048

    statuses = []
    for index in range(20):
        response = await client.post(
            f"/tickets/{ticket}/attachments",
            files={"file": (f"flood-{index}.png", png, "image/png")},
            headers=auth_headers(customer),
        )
        statuses.append(response.status_code)

    assert 429 in statuses


@pytest.mark.xfail(strict=True, reason=GAP)
async def test_assistance_endpoint_is_rate_limited(client, customer, new_ticket, auth_headers):
    """The most expensive route in the system: retrieval, reranking and an LLM
    generation per call, with no per-customer budget."""
    ticket = await new_ticket(customer)

    statuses = []
    for _ in range(15):
        response = await client.post(
            f"/tickets/{ticket}/assistance",
            json={"message": "What is the dispute process?"},
            headers=auth_headers(customer),
        )
        statuses.append(response.status_code)

    assert 429 in statuses


# --- what the app does do today, asserted so a regression is visible -----------


async def test_failed_login_does_not_reveal_whether_the_account_exists(client, customer):
    """User enumeration: both branches must be indistinguishable to the caller."""
    known = await client.post(
        "/auth/login", json={"email": customer.email, "password": "WrongPassword1!"}
    )
    unknown = await client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "WrongPassword1!"}
    )

    assert known.status_code == unknown.status_code == 401
    assert known.json()["detail"] == unknown.json()["detail"]


async def test_oversized_upload_is_refused(client, customer, new_ticket, auth_headers):
    """The one abuse control that does exist: the per-request size cap."""
    ticket = await new_ticket(customer)
    too_big = b"\x89PNG\r\n\x1a\n" + b"0" * (11 * 1024 * 1024)

    response = await client.post(
        f"/tickets/{ticket}/attachments",
        files={"file": ("huge.png", too_big, "image/png")},
        headers=auth_headers(customer),
    )
    assert response.status_code == 413
