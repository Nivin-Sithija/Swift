"""Retain complete model posteriors for dynamic ticket urgency."""

import sqlalchemy as sa

from alembic import op

revision = "0008_prediction_probabilities"
down_revision = "0007_attachment_ocr_text"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("predictions", sa.Column("probabilities", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("predictions", "probabilities")
