"""0004: analysis_runs.verdict_reasons + a wider engine_version (Phase 3).

Revision ID: c81f2a4d9e05
Revises: b7d4e10c92f1
Create Date: 2026-10-17

Phase 3 computes the FR-8 verdict (Verified / Needs Review / Flagged) for every
run and records *why*: ``verdict_reasons`` is a JSON object
``{"verdict": str, "reasons": [str], "not_checked": [str]}`` — reasons list the
findings that drove the verdict and the honest "not checked" states.

``engine_version`` grows from String(50) to String(120) so the run tag can carry
all six engines: ``phase-3|<ocr>|<classifier>|<nlp>|<validator>|<ownership>|<rules>``.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c81f2a4d9e05"
down_revision: Union[str, None] = "b7d4e10c92f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("analysis_runs") as batch_op:
        batch_op.add_column(sa.Column("verdict_reasons", sa.JSON(), nullable=True))
        batch_op.alter_column(
            "engine_version",
            existing_type=sa.String(50),
            type_=sa.String(120),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("analysis_runs") as batch_op:
        batch_op.alter_column(
            "engine_version",
            existing_type=sa.String(120),
            type_=sa.String(50),
            existing_nullable=False,
        )
        batch_op.drop_column("verdict_reasons")
