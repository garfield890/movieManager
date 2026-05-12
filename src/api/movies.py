from fastapi import APIRouter, Depends
from server import decimal_to_float

import sqlalchemy
from src.api import auth
from src import database as db

router = APIRouter(
    prefix="/movies",
    tags=["movies"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/external/search/{title}/{year}", tags=["movies"])
def search_movie(title: str, year: int):
    search_title = title.replace("_", " ")

    with db.engine.begin() as connection:
        rows = connection.execute(
            sqlalchemy.text(
                """
                SELECT movie_id, movie_name, year, imdb_rating
                FROM movies
                WHERE LOWER(movie_name) LIKE LOWER(:title_pattern)
                AND year = :year
                ORDER BY movie_name
                """
            ),
            {
                "title_pattern": f"%{search_title}%",
                "year": year,
            },
        ).mappings().all()

    return {
        "results": [
            {
                "movie_id": row["movie_id"],
                "title": row["movie_name"],
                "release_year": row["year"],
                "imdb_rating": decimal_to_float(row["imdb_rating"]),
            }
            for row in rows
        ]
    }