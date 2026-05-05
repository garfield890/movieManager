from decimal import Decimal

import sqlalchemy
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src import database as db


app = FastAPI(
    title="Movie Manager API",
    summary="Backend API for tracking users and their saved movies.",
    version="0.1.0",
)

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AddCollectionRequest(BaseModel):
    watched: bool = True


class UpdateCollectionRequest(BaseModel):
    watched: bool = True
    rating: float = Field(ge=0, le=10)


def decimal_to_float(value):
    if value is None:
        return None

    if isinstance(value, Decimal):
        return float(value)

    return value


@app.get("/", tags=["meta"])
def read_root() -> dict[str, str]:
    return {
        "service": "movieManager",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"])
def read_health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/users/register", tags=["users"])
def register_user(request: RegisterRequest):
    with db.engine.begin() as connection:
        existing_user = connection.execute(
            sqlalchemy.text(
                """
                SELECT user_id
                FROM users
                WHERE username = :username
                OR email = :email
                """
            ),
            {
                "username": request.username,
                "email": request.email,
            },
        ).mappings().first()

        if existing_user is not None:
            raise HTTPException(
                status_code=400,
                detail="Username or email already exists",
            )

        row = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO users (username, email, password)
                VALUES (:username, :email, :password)
                RETURNING user_id, username
                """
            ),
            {
                "username": request.username,
                "email": request.email,
                "password": request.password,
            },
        ).mappings().one()

    return {
        "user_id": row["user_id"],
        "username": row["username"],
    }


@app.post("/users/login", tags=["users"])
def login_user(request: LoginRequest):
    with db.engine.begin() as connection:
        row = connection.execute(
            sqlalchemy.text(
                """
                SELECT user_id, username
                FROM users
                WHERE username = :username
                AND password = :password
                """
            ),
            {
                "username": request.username,
                "password": request.password,
            },
        ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    return {
        "user_id": row["user_id"],
        "username": row["username"],
        "token": f"v1-demo-token-{row['user_id']}",
    }


@app.get("/movies/external/search/{title}/{year}", tags=["movies"])
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


@app.post("/users/{user_id}/collection/{movie_id}", tags=["collection"])
def add_movie_to_collection(
    user_id: int,
    movie_id: int,
    request: AddCollectionRequest,
):
    with db.engine.begin() as connection:
        user = connection.execute(
            sqlalchemy.text(
                """
                SELECT user_id
                FROM users
                WHERE user_id = :user_id
                """
            ),
            {"user_id": user_id},
        ).mappings().first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        movie = connection.execute(
            sqlalchemy.text(
                """
                SELECT movie_id
                FROM movies
                WHERE movie_id = :movie_id
                """
            ),
            {"movie_id": movie_id},
        ).mappings().first()

        if movie is None:
            raise HTTPException(status_code=404, detail="Movie not found")

        row = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO watched_movies (user_id, movie_id, watch_status, rating)
                VALUES (:user_id, :movie_id, :watch_status, NULL)
                ON CONFLICT (user_id, movie_id) DO UPDATE
                SET watch_status = EXCLUDED.watch_status
                RETURNING user_id, movie_id, watch_status, rating
                """
            ),
            {
                "user_id": user_id,
                "movie_id": movie_id,
                "watch_status": request.watched,
            },
        ).mappings().one()

    return {
        "user_id": row["user_id"],
        "movie_id": row["movie_id"],
        "watched": row["watch_status"],
        "rating": decimal_to_float(row["rating"]),
    }


@app.put("/users/{user_id}/collection/{movie_id}", tags=["collection"])
def update_movie_in_collection(
    user_id: int,
    movie_id: int,
    request: UpdateCollectionRequest,
):
    with db.engine.begin() as connection:
        row = connection.execute(
            sqlalchemy.text(
                """
                UPDATE watched_movies
                SET watch_status = :watch_status,
                    rating = :rating
                WHERE user_id = :user_id
                AND movie_id = :movie_id
                RETURNING user_id, movie_id, watch_status, rating
                """
            ),
            {
                "user_id": user_id,
                "movie_id": movie_id,
                "watch_status": request.watched,
                "rating": request.rating,
            },
        ).mappings().first()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Collection entry not found",
            )

    return {
        "user_id": row["user_id"],
        "movie_id": row["movie_id"],
        "watched": row["watch_status"],
        "rating": decimal_to_float(row["rating"]),
    }


@app.get("/users/{user_id}/collection", tags=["collection"])
def get_user_collection(user_id: int):
    with db.engine.begin() as connection:
        rows = connection.execute(
            sqlalchemy.text(
                """
                SELECT
                    m.movie_id,
                    m.movie_name,
                    m.year,
                    m.imdb_rating,
                    wm.watch_status,
                    wm.rating
                FROM watched_movies wm
                JOIN movies m ON wm.movie_id = m.movie_id
                WHERE wm.user_id = :user_id
                ORDER BY m.movie_name
                """
            ),
            {"user_id": user_id},
        ).mappings().all()

    return {
        "collection": [
            {
                "movie_id": row["movie_id"],
                "title": row["movie_name"],
                "release_year": row["year"],
                "imdb_rating": decimal_to_float(row["imdb_rating"]),
                "watched": row["watch_status"],
                "rating": decimal_to_float(row["rating"]),
            }
            for row in rows
        ]
    }
