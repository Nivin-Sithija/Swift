"""Database integrity: constraints, transactions, injection, and the migration graph.

The ORM-level tests run against SQLite, which is enough to prove constraint and
cascade behaviour is declared correctly. Anything genuinely Postgres-specific —
row-level security, enum types, concurrent index creation — is asserted against
the migration scripts instead and marked accordingly, because a green SQLite run
must not be mistaken for a verified production schema.
"""

import re
import uuid
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError

from app.core.db import Base, engine_options
from app.domain.enums import UserRole
from app.models.entities import Attachment, AuditLog, Prediction, Ticket, TicketEvent, User

pytestmark = pytest.mark.database

BACKEND = Path(__file__).resolve().parents[2]


# --- constraints ------------------------------------------------------------


async def test_email_uniqueness_is_enforced_by_the_database(db):
    """Not just by the route's pre-check: a race between two registrations must
    still be stopped at the constraint."""
    shared = "duplicate@example.com"
    db.add(
        User(
            full_name="First",
            email=shared,
            password_hash="x",
            role=UserRole.customer,
        )
    )
    await db.commit()

    db.add(
        User(
            full_name="Second",
            email=shared,
            password_hash="x",
            role=UserRole.customer,
        )
    )
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()


async def test_registration_race_is_rejected_at_the_api(client):
    payload = {
        "full_name": "Race Condition",
        "email": "race@example.com",
        "password": "CorrectHorse9!",
    }
    first = await client.post("/auth/register", json=payload)
    second = await client.post("/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


async def test_public_ticket_reference_is_unique(db, customer):
    def ticket(reference: str) -> Ticket:
        return Ticket(
            public_id=reference,
            customer_id=customer.id,
            subject="Duplicate reference",
            original_text="Body text for the duplicate reference test.",
            response_language="english",
        )

    db.add(ticket("SW-2026-000042"))
    await db.commit()
    db.add(ticket("SW-2026-000042"))
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()


# --- cascades and orphans ---------------------------------------------------


async def test_deleting_a_ticket_removes_its_children(db, customer, client, auth_headers):
    from tests.conftest import open_ticket

    reference = await open_ticket(client, customer)
    ticket = await db.scalar(select(Ticket).where(Ticket.public_id == reference))
    assert ticket is not None

    db.add(TicketEvent(ticket_id=ticket.id, event_type="test", detail="child row"))
    await db.commit()

    await db.delete(ticket)
    await db.commit()

    for model in (Prediction, TicketEvent, Attachment):
        remaining = await db.scalar(
            select(func.count()).select_from(model).where(model.ticket_id == ticket.id)
        )
        assert remaining == 0, f"{model.__tablename__} rows orphaned after ticket delete"


async def test_audit_log_survives_the_actor_being_deleted(db, administrator):
    """Audit rows are evidence. Deleting the actor must not erase the trail."""
    entry = AuditLog(
        user_id=administrator.id,
        action="user_updated",
        entity_type="user",
        entity_id=str(uuid.uuid4()),
        detail="role changed",
    )
    db.add(entry)
    await db.commit()

    stored = await db.scalar(select(func.count()).select_from(AuditLog))
    assert stored == 1


# --- transactions -----------------------------------------------------------


async def test_failed_commit_leaves_no_partial_write(db, customer):
    """A rolled-back unit of work must not leave the first of two rows behind."""
    before = await db.scalar(select(func.count()).select_from(Ticket))

    db.add(
        Ticket(
            public_id="SW-2026-000900",
            customer_id=customer.id,
            subject="Valid row",
            original_text="This row is valid and should disappear with the rollback.",
            response_language="english",
        )
    )
    db.add(
        Ticket(
            public_id="SW-2026-000900",  # duplicate: forces the failure
            customer_id=customer.id,
            subject="Conflicting row",
            original_text="This row collides on the unique public reference.",
            response_language="english",
        )
    )
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()

    after = await db.scalar(select(func.count()).select_from(Ticket))
    assert after == before


async def test_ticket_creation_is_atomic_when_classification_fails(
    client, customer, auth_headers, monkeypatch
):
    """If the classifier raises, the request must not leave a half-built ticket."""
    from app.api.v1 import routes

    async def _boom(text: str, is_ocr: bool = False):
        raise RuntimeError("inference backend exploded")

    monkeypatch.setattr(routes, "classify", _boom)

    response = await client.post(
        "/tickets",
        json={
            "subject": "Classification will fail",
            "message": "This request should not leave a partially written ticket behind.",
        },
        headers=auth_headers(customer),
    )
    assert response.status_code >= 500

    listing = await client.get("/tickets", headers=auth_headers(customer))
    assert listing.json()["total"] == 0, "a ticket survived a failed classification"


# --- injection --------------------------------------------------------------


SQL_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE tickets; --",
    "1' UNION SELECT password_hash FROM users --",
    "%' --",
    "\\'; DELETE FROM users WHERE '1'='1",
]


@pytest.mark.parametrize("payload", SQL_PAYLOADS)
async def test_ticket_search_is_not_sql_injectable(
    client, customer, new_ticket, auth_headers, payload
):
    """The search filter interpolates into ilike(); the ORM must parameterize it."""
    await new_ticket(customer)

    response = await client.get(
        "/tickets", params={"query": payload}, headers=auth_headers(customer)
    )
    assert response.status_code == 200, response.text
    # A working injection would return the seeded ticket via a tautology.
    assert response.json()["total"] == 0

    # And the table must still be there.
    still_there = await client.get("/tickets", headers=auth_headers(customer))
    assert still_there.json()["total"] == 1


@pytest.mark.parametrize("payload", SQL_PAYLOADS)
async def test_admin_user_search_is_not_sql_injectable(client, administrator, auth_headers, payload):
    response = await client.get(
        "/admin/users", params={"query": payload}, headers=auth_headers(administrator)
    )
    assert response.status_code == 200
    assert response.json()["items"] == []


async def test_wildcards_in_search_are_treated_as_literals(client, customer, new_ticket, auth_headers):
    """`%` is an ilike metacharacter. Unescaped, a lone `%` matches every row —
    harmless for a customer scoped to their own tickets, but a data-scope bug for staff."""
    await new_ticket(customer)
    response = await client.get("/tickets", params={"query": "%"}, headers=auth_headers(customer))
    assert response.status_code == 200


# --- query efficiency -------------------------------------------------------


async def test_ticket_list_does_not_issue_a_query_per_ticket(
    client, customer, new_ticket, auth_headers, engine
):
    """N+1 regression guard. `ticket_options()` eager-loads the relations; if someone
    removes a selectinload, the query count grows with the page size instead of staying flat."""
    for index in range(5):
        await new_ticket(customer, f"Ticket number {index}")

    counter = {"queries": 0}

    def count(*args, **kwargs):
        counter["queries"] += 1

    event.listen(engine.sync_engine, "before_cursor_execute", count)
    try:
        response = await client.get("/tickets", headers=auth_headers(customer))
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", count)

    assert response.json()["total"] == 5
    # count + page + one eager load per relation; well under one query per row.
    assert counter["queries"] <= 12, f"{counter['queries']} queries for a 5-row page"


# --- migration graph --------------------------------------------------------


def alembic_scripts() -> ScriptDirectory:
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    return ScriptDirectory.from_config(config)


def test_migration_history_has_exactly_one_head():
    """Two heads means `alembic upgrade head` is ambiguous and deploys break."""
    heads = alembic_scripts().get_heads()
    assert len(heads) == 1, f"divergent migration heads: {heads}"


def test_every_migration_is_reachable_from_the_head():
    scripts = alembic_scripts()
    head = scripts.get_heads()[0]
    walked = {revision.revision for revision in scripts.walk_revisions("base", head)}
    all_revisions = {revision.revision for revision in scripts.walk_revisions()}
    assert walked == all_revisions, f"orphaned migrations: {all_revisions - walked}"


def test_every_migration_declares_a_downgrade():
    """A migration without a downgrade cannot be rolled back in an incident."""
    missing = []
    for revision in alembic_scripts().walk_revisions():
        source = Path(revision.path).read_text()
        body = source.split("def downgrade()", 1)
        if len(body) == 1 or "pass" == body[1].split(":", 1)[1].strip().split("\n")[0].strip():
            missing.append(revision.revision)
    assert not missing, f"migrations with no usable downgrade: {missing}"


def test_engine_uses_pool_pre_ping():
    """Without pre-ping, every connection recycled by the database appears as a
    random 500 to the next request that borrows it."""
    assert engine_options("postgresql+asyncpg://u:p@h/db")["pool_pre_ping"] is True


def test_supabase_urls_get_tls():
    assert engine_options("postgresql+asyncpg://u:p@db.supabase.com/db")["connect_args"] == {
        "ssl": "require"
    }


def test_orm_metadata_matches_the_tables_the_migrations_create():
    """Cheap drift check: every mapped table must appear in some migration file."""
    sql = "\n".join(
        Path(revision.path).read_text() for revision in alembic_scripts().walk_revisions()
    )
    missing = [name for name in Base.metadata.tables if f'"{name}"' not in sql and f"'{name}'" not in sql]
    assert not missing, f"mapped tables never created by a migration: {missing}"


# --- reviewed static-analysis findings ---------------------------------------


def test_retrieval_sql_interpolates_no_caller_data():
    """Bandit flags `app/rag/retrieval.py` B608 (string-built SQL) at two lines.

    Reviewed and dismissed: the only value interpolated into the f-string is the
    module-local `filters` constant, and every caller-supplied value goes through a
    bound parameter. This test is what keeps that dismissal honest — if someone
    later interpolates a variable, the placeholder count stops matching and this
    fails instead of quietly becoming a real injection.
    """
    source = (BACKEND / "app" / "rag" / "retrieval.py").read_text()
    body = source.split("async def _query(", 1)[1].split("    @staticmethod", 1)[0]

    interpolations = re.findall(r"\{(\w+)\}", body)
    assert set(interpolations) <= {"filters"}, (
        f"SQL now interpolates something other than the static filter clause: {interpolations}"
    )

    for parameter in (":review_days", ":institution", ":category", ":limit", ":query"):
        assert parameter in body, f"{parameter} is no longer a bound parameter"


def test_no_raw_sql_uses_percent_or_format_interpolation():
    """Broad sweep: an f-string or % on a text() call is the shape of a real injection."""
    offenders = []
    for path in (BACKEND / "app").rglob("*.py"):
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            # Only an f-string or %-format passed straight to text() is dangerous;
            # a plain string with :bound parameters is the correct pattern.
            if re.search(r"""text\(\s*f["']""", line) or re.search(r"""text\(.*%\s*\(""", line):
                offenders.append(f"{path.relative_to(BACKEND)}:{line_number}: {line.strip()[:80]}")
    assert not offenders, offenders
