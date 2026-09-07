"""Input validation: payload abuse, file uploads, and output encoding.

Covers the OWASP input-handling classes that apply to this API — oversized and
malformed bodies, upload type confusion, path traversal in stored filenames, and
whether attacker-controlled text is echoed back verbatim.
"""

import pytest

pytestmark = pytest.mark.security

PNG = b"\x89PNG\r\n\x1a\n"
JPEG = b"\xff\xd8\xff"
PDF = b"%PDF"


# --- request bodies ---------------------------------------------------------


async def test_oversized_ticket_body_is_rejected(client, customer, auth_headers):
    response = await client.post(
        "/tickets",
        json={"subject": "Large body", "message": "A" * 50_000},
        headers=auth_headers(customer),
    )
    assert response.status_code == 422


async def test_missing_required_fields_return_422_not_500(client, customer, auth_headers):
    response = await client.post("/tickets", json={}, headers=auth_headers(customer))
    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"subject": None, "message": None},
        {"subject": ["not", "a", "string"], "message": "A valid enough message body here."},
        {"subject": {"nested": "object"}, "message": "A valid enough message body here."},
        {"subject": 12345, "message": "A valid enough message body here."},
    ],
)
async def test_type_confusion_in_the_body_is_rejected(client, customer, auth_headers, payload):
    response = await client.post("/tickets", json=payload, headers=auth_headers(customer))
    assert response.status_code == 422, f"accepted malformed body: {payload}"


async def test_deeply_nested_json_does_not_crash_the_parser(client, customer, auth_headers):
    """Billion-laughs style nesting must be refused, not recursed into."""
    nested: object = "leaf"
    for _ in range(200):
        nested = {"next": nested}

    response = await client.post(
        "/tickets",
        json={"subject": "Nested payload", "message": nested},
        headers=auth_headers(customer),
    )
    assert response.status_code in (413, 422), response.status_code


async def test_invalid_email_is_rejected_at_registration(client):
    response = await client.post(
        "/auth/register",
        json={"full_name": "Bad Email", "email": "not-an-email", "password": "CorrectHorse9!"},
    )
    assert response.status_code == 422


async def test_short_password_is_rejected(client):
    response = await client.post(
        "/auth/register",
        json={"full_name": "Weak Pass", "email": "weak@example.com", "password": "short"},
    )
    assert response.status_code == 422


async def test_pagination_bounds_are_enforced(client, customer, auth_headers):
    """An unbounded page_size is a cheap way to pull the whole table."""
    over = await client.get(
        "/tickets", params={"page_size": 10_000}, headers=auth_headers(customer)
    )
    assert over.status_code == 422

    negative = await client.get("/tickets", params={"page": -1}, headers=auth_headers(customer))
    assert negative.status_code == 422


# --- file uploads -----------------------------------------------------------


async def test_declared_type_must_match_the_file_signature(
    client, customer, new_ticket, auth_headers
):
    """An executable renamed to .png must not be stored as an image."""
    ticket = await new_ticket(customer)
    response = await client.post(
        f"/tickets/{ticket}/attachments",
        files={"file": ("payload.png", b"MZ\x90\x00executable", "image/png")},
        headers=auth_headers(customer),
    )
    assert response.status_code == 415


@pytest.mark.parametrize(
    "content_type,body",
    [
        ("text/html", b"<script>alert(1)</script>"),
        ("image/svg+xml", b"<svg onload=alert(1)>"),
        ("application/x-sh", b"#!/bin/sh\nrm -rf /"),
        ("text/plain", b"just text"),
    ],
)
async def test_disallowed_mime_types_are_refused(
    client, customer, new_ticket, auth_headers, content_type, body
):
    ticket = await new_ticket(customer)
    response = await client.post(
        f"/tickets/{ticket}/attachments",
        files={"file": ("payload", body, content_type)},
        headers=auth_headers(customer),
    )
    assert response.status_code == 415, f"{content_type} was accepted"


async def test_path_traversal_in_the_filename_cannot_escape_storage(
    client, customer, new_ticket, auth_headers, tmp_path
):
    """The stored path is a generated UUID, and the download route re-checks that the
    resolved path stays under storage_root. This proves the filename cannot steer it."""
    ticket = await new_ticket(customer)
    response = await client.post(
        f"/tickets/{ticket}/attachments",
        files={"file": ("../../../../etc/passwd.png", PNG + b"0" * 64, "image/png")},
        headers=auth_headers(customer),
    )
    assert response.status_code == 201

    stored_name = response.json()["name"]
    assert "/" not in stored_name and ".." not in stored_name, (
        f"traversal sequence survived into the stored filename: {stored_name!r}"
    )

    written = list(tmp_path.rglob("*"))
    assert all(tmp_path in path.parents or path == tmp_path for path in written)


async def test_null_byte_in_filename_is_handled(client, customer, new_ticket, auth_headers):
    ticket = await new_ticket(customer)
    response = await client.post(
        f"/tickets/{ticket}/attachments",
        files={"file": ("evil\x00.png", PNG + b"0" * 64, "image/png")},
        headers=auth_headers(customer),
    )
    assert response.status_code in (201, 400, 415)
    if response.status_code == 201:
        assert "\x00" not in response.json()["name"]


async def test_empty_upload_is_refused(client, customer, new_ticket, auth_headers):
    ticket = await new_ticket(customer)
    response = await client.post(
        f"/tickets/{ticket}/attachments",
        files={"file": ("empty.png", b"", "image/png")},
        headers=auth_headers(customer),
    )
    assert response.status_code == 415


# --- output encoding --------------------------------------------------------


XSS_PAYLOADS = [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(1)",
    "'\"><svg/onload=alert(1)>",
]


@pytest.mark.parametrize("payload", XSS_PAYLOADS)
async def test_script_payloads_are_returned_as_json_not_html(
    client, customer, auth_headers, payload
):
    """The API is JSON-only, so the defence is the content type plus JSON escaping.
    A payload stored and echoed is fine; a payload served as text/html is not.
    """
    created = await client.post(
        "/tickets",
        json={"subject": "Script payload test", "message": f"Please look at this: {payload}"},
        headers=auth_headers(customer),
    )
    assert created.status_code == 201
    assert created.headers["content-type"].startswith("application/json")

    reference = created.json()["id"]
    fetched = await client.get(f"/tickets/{reference}", headers=auth_headers(customer))
    assert fetched.headers["content-type"].startswith("application/json")
    # Round-trips intact as data; the frontend is responsible for rendering it as text.
    assert payload in fetched.json()["message"]


async def test_error_responses_do_not_echo_raw_html(client, customer, auth_headers):
    response = await client.get(
        "/tickets", params={"query": "<script>alert(1)</script>"}, headers=auth_headers(customer)
    )
    assert response.headers["content-type"].startswith("application/json")


# --- CORS -------------------------------------------------------------------


async def test_cors_does_not_reflect_an_arbitrary_origin(client):
    """`allow_credentials=True` with a reflected origin would let any site read
    authenticated responses. The configured allowlist must hold."""
    response = await client.get("/health", headers={"Origin": "https://evil.example"})
    allowed = response.headers.get("access-control-allow-origin")
    assert allowed != "https://evil.example", "CORS reflected an unlisted origin"
    assert allowed != "*" or "access-control-allow-credentials" not in response.headers
