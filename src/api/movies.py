from fastapi import APIRouter, Depends, HTTPException
from src.misc import decimal_to_float
from pydantic import BaseModel

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
                SELECT movies.movie_id, movies.movie_name, movies.year AS release_year, movies.imdb_rating, movies.runtime, movies.mpaa_rating, movies.plot, COUNT(*) as watch_count
                FROM movies
                JOIN watched_movies wm ON wm.movie_id = movies.movie_id
                WHERE wm.date_added >= CURRENT_DATE - :days
                GROUP BY movies.movie_id, movies.movie_name, movies.year, movies.imdb_rating, movies.runtime, movies.mpaa_rating, movies.plot
                ORDER BY watch_count DESC
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