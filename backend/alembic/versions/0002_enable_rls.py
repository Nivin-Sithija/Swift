"""Protect application tables exposed through Supabase's public schema."""

from alembic import op

revision = "0002_enable_rls"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

TABLES = (
    "users",
    "auth_sessions",
    "support_queues",
    "ticket_categories",
    "tickets",
    "ticket_events",
    "ticket_notes",
    "predictions",
    "attachments",
    "processing_jobs",
    "responses",
    "audit_logs",
)


def upgrade() -> None:
    # Swift authorizes requests in FastAPI and connects as the database owner.
    # Enabling RLS without Data API policies blocks anon/authenticated API access.
    for table in TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    for table in TABLES:
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
