"""Merge the supervisor role into administrator."""

import sqlalchemy as sa
from alembic import op

revision = "0003_merge_roles"
down_revision = "0002_enable_rls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    has_supervisor = bind.execute(
        sa.text(
            "SELECT 1 FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid "
            "WHERE t.typname = 'userrole' AND e.enumlabel = 'supervisor'"
        )
    ).first()
    if has_supervisor:
        op.execute("UPDATE users SET role = 'administrator' WHERE role = 'supervisor'")
    op.execute("ALTER TYPE userrole RENAME TO userrole_old")
    op.execute("CREATE TYPE userrole AS ENUM ('customer', 'agent', 'administrator')")
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE userrole "
        "USING role::text::userrole"
    )
    op.execute("DROP TYPE userrole_old")


def downgrade() -> None:
    op.execute("ALTER TYPE userrole RENAME TO userrole_old")
    op.execute(
        "CREATE TYPE userrole AS ENUM "
        "('customer', 'agent', 'supervisor', 'administrator')"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE userrole "
        "USING role::text::userrole"
    )
    op.execute("DROP TYPE userrole_old")
