"""initial schema

Revision ID: 0001
Revises:
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "games",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sandbox_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sandbox_id", sa.Text(), nullable=True),
        sa.Column(
            "lifecycle_state",
            sa.Text(),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column("snapshot_key", sa.Text(), nullable=True),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("snapshot_bytes", sa.BigInteger(), nullable=True),
        sa.Column("snapshot_sha256", sa.Text(), nullable=True),
        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("archive_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archive_attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "lifecycle_state IN ('active', 'archiving', 'archived', 'restoring')",
            name="sandbox_sessions_state_check",
        ),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "sandbox_sessions_game_idx", "sandbox_sessions", ["game_id"], unique=True
    )
    op.create_index(
        "sandbox_sessions_last_used_idx", "sandbox_sessions", ["last_used_at"]
    )
    op.create_index(
        "sandbox_sessions_retry_idx", "sandbox_sessions", ["archive_retry_at"]
    )


def downgrade() -> None:
    op.drop_index("sandbox_sessions_retry_idx", table_name="sandbox_sessions")
    op.drop_index("sandbox_sessions_last_used_idx", table_name="sandbox_sessions")
    op.drop_index("sandbox_sessions_game_idx", table_name="sandbox_sessions")
    op.drop_table("sandbox_sessions")
    op.drop_table("games")
