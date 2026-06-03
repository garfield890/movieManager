from fastapi import APIRouter, Depends, HTTPException, Query
from src.misc import GENRE_ALIASES, decimal_to_float
from pydantic import BaseModel
from typing import Literal

import sqlalchemy
from src.api import auth
from src import database as db

router = APIRouter(
    prefix="/movies",
    tags=["movies"],
    dependencies=[Depends(auth.get_api_key)],
)

class TrendingEntryResponse(BaseModel):
    movie_id: int
    title: str
    release_year: int | None
    imdb_rating: float | None
    runtime: int | None
    mpaa_rating: str | None
    plot: str | None

class TrendingResponse(BaseModel):
    trending_movies: list[TrendingEntryResponse]

class LeaderboardEntryResponse(BaseModel):
    rank: int
    user_id: int
    username: str
    movies_watched: int
    hours_watched: float | None
    average_rating: float | None

class LeaderboardResponse(BaseModel):
    sort_by: str
    genre: str | None
    leaderboard: list[LeaderboardEntryResponse]

@router.get("/external/search/{title}/{year}", tags=["movies"])
def search_movie(title: str, year: int):
    search_title = title.replace("_", " ")

    with db.engine.begin() as connection:
        movie = connection.execute(
            sqlalchemy.text(
                """
                SELECT movie_id, movie_name, year, imdb_rating, runtime, mpaa_rating, plot
                FROM movies
                WHERE movie_name = :title
                AND year = :year
                """
            ),
            {
                "title": search_title,
                "year": year,
            },
        ).mappings().first()

        if movie is None:
            other_years = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT year
                    FROM movies
                    WHERE movie_name = :title
                    ORDER BY year
                    LIMIT 3;
                    """
                ),
                {"title": search_title},
            ).scalars().all()

            if other_years:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "message": f"No movie found for '{search_title}' in {year}.",
                        "available_years": other_years,
                    },
                )

            raise HTTPException(status_code=404, detail="Movie not found. Please check the movie name and release year and enter it again. ")

    return {
        "results": [
            {
                "movie_id": movie["movie_id"],
                "title": movie["movie_name"],
                "release_year": movie["year"],
                "imdb_rating": decimal_to_float(movie["imdb_rating"]),
                "runtime": movie["runtime"],
                "mpaa_rating": movie["mpaa_rating"],
                "plot": movie["plot"],
            }
        ]
    }

@router.get("/trending/{days}")
def get_trending_movies(days: int):
    with db.engine.begin() as connection:
        trending = connection.execute(
            sqlalchemy.text(
                """
                WITH trending_counts AS (
                    SELECT wm.movie_id, COUNT(*) AS watch_count
                    FROM watched_movies wm
                    WHERE wm.date_added >= CURRENT_DATE - :days
                    GROUP BY wm.movie_id
                    ORDER BY watch_count DESC
                    LIMIT 20
                )
                SELECT
                    m.movie_id,
                    m.movie_name,
                    m.year AS release_year,
                    m.imdb_rating,
                    m.runtime,
                    m.mpaa_rating,
                    m.plot,
                    tc.watch_count
                FROM trending_counts tc
                JOIN movies m ON m.movie_id = tc.movie_id
                ORDER BY tc.watch_count DESC
                """
            ),
            {"days": days},
        ).mappings().all()

        if not trending:
            raise HTTPException(status_code=404, detail="No trending movies within day range. Try a larger day range or add some movies.")

    return {
        "trending_movies": [
            {
                "movie_id": row["movie_id"],
                "title": row["movie_name"],
                "release_year": row["release_year"],
                "imdb_rating": decimal_to_float(row["imdb_rating"]),
                "runtime": row["runtime"],
                "mpaa_rating": row["mpaa_rating"],
                "plot": row["plot"],
            }
            for row in trending
        ]
    }
LEADERBOARD_SORT_COLUMNS = {
    "movies_watched": "COUNT(*)",
    "hours_watched": "COALESCE(SUM(m.runtime), 0) / 60.0",
    "average_rating": "ROUND(AVG(wm.rating)::numeric, 2)",
    "movies_rated": "COUNT(wm.rating)",
    "highest_rated_movie": "MAX(wm.rating)",
}

@router.get("/leaderboard/{genre}/{limit}", response_model=LeaderboardResponse)
def get_leaderboard(
    genre: str, 
    limit: int, 
    sort_by: Literal["movies_watched", "hours_watched", "average_rating", "movies_rated", "highest_rated_movie"] = Query(default="movies_watched")
):
    order_col = LEADERBOARD_SORT_COLUMNS[sort_by]
    genre = GENRE_ALIASES.get(genre.lower(), '')

    with db.engine.begin() as connection:
        rows = connection.execute(
            sqlalchemy.text(
                f"""
                SELECT
                    u.user_id,
                    u.username,
                    COUNT(*) AS movies_watched,
                    ROUND(COALESCE(SUM(m.runtime), 0) / 60.0, 1) AS hours_watched,
                    ROUND(AVG(wm.rating), 2) AS average_rating
                FROM users u
                JOIN watched_movies wm ON wm.user_id = u.user_id
                JOIN movies m ON m.movie_id = wm.movie_id
                WHERE wm.watched = TRUE
                  AND (:genre = '' OR EXISTS (
                      SELECT 1 FROM movie_genres mg
                      JOIN genres g ON g.genre_id = mg.genre_id
                      WHERE mg.movie_id = m.movie_id AND g.genre_name = :genre
                  ))
                GROUP BY u.user_id, u.username
                ORDER BY {order_col} DESC NULLS LAST
                LIMIT :limit
                """
            ),
            {"genre": genre, "limit": limit},
        ).mappings().all()

    return {
        "sort_by": sort_by,
        "genre": genre if genre else None,
        "leaderboard": [
            {
                "rank": idx + 1,
                "user_id": row["user_id"],
                "username": row["username"],
                "movies_watched": row["movies_watched"],
                "hours_watched": decimal_to_float(row["hours_watched"]),
                "average_rating": decimal_to_float(row["average_rating"]),
            }
            for idx, row in enumerate(rows)
        ],
    }
