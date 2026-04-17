"""questions table

Revision ID: 0003_questions
Revises: 0002_documents
Create Date: 2026-04-17
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_questions"
down_revision: str | None = "0002_documents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "questions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("deal_room_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["deal_room_id"], ["deal_rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_questions_deal_room_id", "questions", ["deal_room_id"])
    op.create_index("ix_questions_user_id", "questions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_questions_user_id", table_name="questions")
    op.drop_index("ix_questions_deal_room_id", table_name="questions")
    op.drop_table("questions")
