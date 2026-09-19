"""Store masked OCR text on the attachment instead of appending it to the ticket text."""

import sqlalchemy as sa

from alembic import op

revision = "0007_attachment_ocr_text"
down_revision = "0006_consumer_rag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("attachments", sa.Column("ocr_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("attachments", "ocr_text")
