"""add trending performance index

Revision ID: b7f4c2a9012d
Revises: a6e76ca47bf1
Create Date: 2026-06-01 23:10:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b7f4c2a9012d"
down_revision: Union[str, None] = "a6e76ca47bf1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_watched_movies_movie_id_date_added
        ON watched_movies (movie_id, date_added)
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        """
        DROP INDEX IF EXISTS idx_watched_movies_movie_id_date_added
        """
    )
