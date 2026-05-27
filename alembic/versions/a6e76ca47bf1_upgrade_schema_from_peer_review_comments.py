"""Upgrade schema from peer review comments

Revision ID: a6e76ca47bf1
Revises: 8978a68e5b62
Create Date: 2026-05-26 15:06:46.951908

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6e76ca47bf1'
down_revision: Union[str, None] = '8978a68e5b62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "logins",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="CASCADE"),primary_key=True),
        sa.Column("login_token", sa.String(), nullable=False, unique=True),
    )

    op.create_table(
        "failed_genre_aliases",
        sa.Column("id", sa.Identity(), nullable=False, primary_key=True),
        sa.Column("alias", sa.String(), nullable=False, primary_key=False)
    )

    op.alter_column(
        "watched_movies",
        "watch_status",
        new_column_name="watched"
    )

    op.add_column(
        "users",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.add_column(
        "watched_movies",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.add_column(
        "watched_movies",
        sa.Column(
            "date_added",
            sa.Date(),
            server_default=sa.text("CURRENT_DATE"),
            nullable=False
        )
    )

    op.add_column(
        "movies",
        sa.Column(
            "runtime",
            sa.Integer(),
            server_default=0,
            nullable=False
        )
    )

    op.add_column(
        "movies",
        sa.Column(
            "mpaa_rating",
            sa.String(),
            server_default="PG-13",
            nullable=False
        )
    )

    op.add_column(
        "movies",
        sa.Column(
            "plot",
            sa.String(),
            server_default="",
            nullable=False
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("logins")
    op.drop_table("failed_genre_aliases")
    op.alter_column(
        "watched_movies",
        "watched",
        new_column_name="watch_status"
    )
    op.drop_column("users", "created_at")
    op.drop_column("watched_movies", "updated_at")
    op.drop_column("watched_movies", "date_added")