"""0006: reviewer workflow and per-run review history (Phase 6).

Adds the human-review state to analysis runs and findings:

* ``analysis_runs.review_status`` - pending / confirmed / overridden;
* ``analysis_runs.review_verdict`` - the human-final verdict when overridden;
* ``analysis_runs.reviewed_by`` / ``reviewed_at`` / ``review_note``;
* ``risk_flags.reviewed_by`` / ``reviewed_at`` / ``review_note`` alongside the
  existing ``status`` column (open / confirmed / dismissed / needs_evidence).

The findings and ownership rows of older runs are no longer deleted on re-run,
so a reviewer's decisions remain attached to the run they reviewed.

Revision ID: e5c9a7b31f42
Revises: d4b8c1f2a6e7
Create Date: 2026-10-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5c9a7b31f42"
down_revision: Union[str, None] = "d4b8c1f2a6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("risk_flags") as batch_op:
        batch_op.add_column(sa.Column("reviewed_by", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("review_note", sa.Text(), nullable=True))

    with op.batch_alter_table("analysis_runs") as batch_op:
        batch_op.add_column(
            sa.Column("review_status", sa.String(32), nullable=False, server_default="pending")
        )
        batch_op.add_column(sa.Column("review_verdict", sa.String(32), nullable=True))
        batch_op.add_column(sa.Column("reviewed_by", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("review_note", sa.Text(), nullable=True))

    op.create_index(
        "ix_analysis_runs_review_status", "analysis_runs", ["review_status"], unique=False
    )
    op.create_index("ix_risk_flags_status", "risk_flags", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_risk_flags_status", table_name="risk_flags")
    op.drop_index("ix_analysis_runs_review_status", table_name="analysis_runs")

    with op.batch_alter_table("analysis_runs") as batch_op:
        batch_op.drop_column("review_note")
        batch_op.drop_column("reviewed_at")
        batch_op.drop_column("reviewed_by")
        batch_op.drop_column("review_verdict")
        batch_op.drop_column("review_status")

    with op.batch_alter_table("risk_flags") as batch_op:
        batch_op.drop_column("review_note")
        batch_op.drop_column("reviewed_at")
        batch_op.drop_column("reviewed_by")
