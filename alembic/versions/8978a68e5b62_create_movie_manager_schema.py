"""create movie manager schema

Revision ID: 8978a68e5b62
Revises: 
Create Date: 2026-05-04 21:51:17.569263

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8978a68e5b62'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.Text(), nullable=False, unique=True),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("password", sa.Text(), nullable=False),
    )

    op.create_table(
        "movies",
        sa.Column("movie_id", sa.Integer(), primary_key=True),
        sa.Column("movie_name", sa.Text(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("imdb_rating", sa.Numeric(3, 1), nullable=True),
        sa.UniqueConstraint("movie_name", "year", name="uq_movies_name_year"),
    )

    op.create_table(
        "directors",
        sa.Column("director_id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
    )

    op.create_table(
        "actors",
        sa.Column("actor_id", sa.Integer(), primary_key=True),
        sa.Column("actor_name", sa.Text(), nullable=False, unique=True),
    )

    op.create_table(
        "genres",
        sa.Column("genre_id", sa.Integer(), primary_key=True),
        sa.Column("genre_name", sa.Text(), nullable=False, unique=True),
    )

    op.create_table(
        "watched_movies",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.movie_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("watch_status", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rating", sa.Numeric(3, 1), nullable=True),
        sa.CheckConstraint("rating IS NULL OR (rating >= 0 AND rating <= 10)", name="ck_watched_movies_rating_range"),
    )

    op.create_table(
        "movie_actors",
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.movie_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("actors.actor_id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "movie_directors",
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.movie_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("director_id", sa.Integer(), sa.ForeignKey("directors.director_id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "movie_genres",
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.movie_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("genre_id", sa.Integer(), sa.ForeignKey("genres.genre_id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("movie_genres")
    op.drop_table("movie_directors")
    op.drop_table("movie_actors")
    op.drop_table("watched_movies")
    op.drop_table("genres")
    op.drop_table("actors")
    op.drop_table("directors")
    op.drop_table("movies")
    op.drop_table("users")