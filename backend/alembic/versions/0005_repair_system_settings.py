"""Repair databases where revision 0004 was recorded before its table was added."""

import sqlalchemy as sa
from alembic import op

revision = "0005_repair_settings"
down_revision = "0004_admin_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "system_settings" not in inspector.get_table_names():
        op.create_table(
            "system_settings",
            sa.Column("key", sa.String(100), primary_key=True),
            sa.Column("value", sa.Text(), nullable=False),
            sa.Column("value_type", sa.String(20), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("updated_by", sa.Uuid(), sa.ForeignKey("users.id")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.execute('ALTER TABLE "system_settings" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    # The table belongs to revision 0004; rolling back this repair must not
    # remove data from databases where 0004 created it normally.
    pass
