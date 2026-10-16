"""0003: documents.ocr_pages — per-page OCR output (Phase 2).

Revision ID: b7d4e10c92f1
Revises: da76db51cad1
Create Date: 2026-10-17

Phase 2 stores every page's OCR text + confidence next to the joined
``ocr_text`` blob so findings can cite page-level evidence (Specs p.2
"Explainable AI": evidence/document page where available). The column is
``sa.JSON()`` (JSONB on PostgreSQL, as in 0002) and holds a list of
``{"page": int, "text": str, "confidence": float | None}`` objects.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7d4e10c92f1"
down_revision: Union[str, None] = "da76db51cad1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.add_column(sa.Column("ocr_pages", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_column("ocr_pages")
