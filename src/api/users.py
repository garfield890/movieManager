from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from src.misc import GENRE_ALIASES, decimal_to_float, normalize_person

import sqlalchemy
from src.api import auth
from src import database as db

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(auth.get_api_key)],
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

@router.post("/register", tags=["users"])
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


@router.post("/login", tags=["users"])
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

@router.post("/{user_id}/collection/{movie_id}", tags=["collection"])
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

@router.put("/{user_id}/collection/{movie_id}", tags=["collection"])
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

@router.post("/{user_id}/collection/{movie_id}/remove", tags=["collection"])
def remove_movie_from_collection(
    user_id: int,
    movie_id: int, 
):
    with db.engine.begin() as connection:
        movie_name = connection.execute(
            sqlalchemy.text(
                """
                SELECT movie_name
                FROM movies
                WHERE movie_id = :movie_id
                """
            ),
            {"movie_id": movie_id}
        ).scalar_one_or_none()

        if movie_name is None:
           raise HTTPException(status_code=404, detail="Movie not found.") 

        connection.execute(
            sqlalchemy.text(
                """
                DELETE FROM watched_movies wm
                WHERE wm.movie_id = :movie_id AND wm.user_id = :user_id
                """
            ),
            {
                "user_id": user_id,
                "movie_id": movie_id
            }
        )
    
    return {
        "user_id": user_id,
        "movie_name": movie_name,
        "removed": True
    }

@router.get("/{user_id}/collection", tags=["collection"])
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

@router.get("/{user_id}/collection/filter/genre/{genre}", tags=["collection"])
def filter_movie_collection_by_genre(user_id: int, genre: str):
    genre = GENRE_ALIASES.get(genre)
    with db.engine.begin() as connection:
        genre_id = connection.execute(
            sqlalchemy.text(
                """
                SELECT genre_id
                FROM genres
                WHERE genre_name = :genre
                """
            ),
            {"genre": genre}
        ).scalar_one_or_none()

        if genre_id is None:
          raise HTTPException(status_code=404, detail="Genre not found.")

        result = connection.execute(
            sqlalchemy.text(
                """
                SELECT movies.movie_id, movies.movie_name, movies.year AS movie_year, wm.rating, g.genre_name
                FROM watched_movies wm
                JOIN movies ON wm.movie_id = movies.movie_id
                JOIN movie_genres mg ON mg.movie_id = movies.movie_id
                JOIN genres g ON g.genre_id = mg.genre_id
                WHERE wm.user_id = :user_id AND g.genre_id = :genre_id
                ORDER BY wm.rating DESC
                """
            ),
            {
                "user_id": user_id,
                "genre_id": genre_id
            }
        ).mappings().all()

    return {
        "collection": [
            {
                "movie_id": row["movie_id"],
                "movie_title": row["movie_name"],
                "release_year": row["movie_year"],
                "rating": decimal_to_float(row["rating"]),
                "genre": row["genre_name"] 
            }
            for row in result
        ]
    }

@router.get("/{user_id}/collection/filter/director/{director}", tags=["collection"])
def filter_movie_collection_by_director(user_id: int, director: str):
    director = normalize_person(director)
    with db.engine.begin() as connection:
        director_id = connection.execute(
            sqlalchemy.text(
                """
                SELECT director_id
                FROM directors
                WHERE name = :director
                """
            ),
            {"director": director}
        ).scalar_one_or_none()

        if director_id is None:
          raise HTTPException(status_code=404, detail="Director not found.")

        result = connection.execute(
            sqlalchemy.text(
                """
                SELECT movies.movie_id, movies.movie_name, movies.year AS movie_year, wm.rating, d.name AS director_name
                FROM watched_movies wm
                JOIN movies ON wm.movie_id = movies.movie_id
                JOIN movie_directors md ON md.movie_id = movies.movie_id
                JOIN directors d ON d.director_id = md.director_id
                WHERE wm.user_id = :user_id AND d.director_id = :director_id
                ORDER BY wm.rating DESC
                """
            ),
            {
                "user_id": user_id,
                "director_id": director_id
            }
        ).mappings().all()

    return {
        "collection": [
            {
                "movie_id": row["movie_id"],
                "movie_title": row["movie_name"],
                "release_year": row["movie_year"],
                "rating": decimal_to_float(row["rating"]),
                "director": row["director_name"] 
            }
            for row in result
        ]
    }

@router.get("/{user_id}/collection/filter/actor/{actor}", tags=["collection"])
def filter_movie_collection_by_actor(user_id: int, actor: str):
    actor = normalize_person(actor)
    with db.engine.begin() as connection:
        actor_id = connection.execute(
            sqlalchemy.text(
                """
                SELECT actor_id
                FROM actors
                WHERE actor_name = :actor
                """
            ),
            {"actor": actor}
        ).scalar_one_or_none()

        if actor_id is None:
          raise HTTPException(status_code=404, detail="Actor not found.")

        result = connection.execute(
            sqlalchemy.text(
                """
                SELECT movies.movie_id, movies.movie_name, movies.year AS movie_year, wm.rating, a.actor_name AS actor_name
                FROM watched_movies wm
                JOIN movies ON wm.movie_id = movies.movie_id
                JOIN movie_actors ma ON ma.movie_id = movies.movie_id
                JOIN actors a ON a.actor_id = ma.actor_id
                WHERE wm.user_id = :user_id AND a.actor_id = :actor_id
                ORDER BY wm.rating DESC
                """
            ),
            {
                "user_id": user_id,
                "actor_id": actor_id
            }
        ).mappings().all()

    return {
        "collection": [
            {
                "movie_id": row["movie_id"],
                "movie_title": row["movie_name"],
                "release_year": row["movie_year"],
                "rating": decimal_to_float(row["rating"]),
                "actor": row["actor_name"] 
            }
            for row in result
        ]
    }

@router.get("/{user_id}/recommendations", tags=["collection"])
def recommend_movies(user_id: int):
    with db.engine.begin() as connection:
        top_unwatched = connection.execute(
            sqlalchemy.text(
                """
                SELECT m.movie_id, m.movie_name, m.year, m.imdb_rating
                FROM movies m
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM watched_movies wm
                    WHERE wm.user_id = :user_id
                      AND wm.movie_id = m.movie_id
                )
                ORDER BY m.imdb_rating DESC NULLS LAST
                LIMIT 5
                """
            ),
            {"user_id": user_id}
        ).mappings().all()

        watched_movies = connection.execute(
            sqlalchemy.text(
                """
                SELECT COUNT(*)
                FROM watched_movies wm
                WHERE wm.user_id = :user_id
                """
            ),
            { "user_id": user_id}
        ).scalar_one()

        if watched_movies < 5:
            return {
                "description": "Not enough movies watched to provide personalized recommendations. Here are the top unwatched movies.",
                "collection": [
                    {
                        "movie_id": row["movie_id"],
                        "movie_name": row["movie_name"],
                        "release_year": row["year"],
                        "imdb_rating": decimal_to_float(row["imdb_rating"])
                    }
                    for row in top_unwatched
                ]
            }
        
        recs = connection.execute(
            sqlalchemy.text(
                """
                WITH user_genre_preferences AS (
                    SELECT mg.genre_id, AVG(wm.rating) AS avg_genre_rating
                    FROM watched_movies wm
                    JOIN movie_genres mg ON wm.movie_id = mg.movie_id
                    WHERE wm.user_id = :user_id AND wm.rating IS NOT NULL
                    GROUP BY mg.genre_id
                ),
                unwatched_movies AS (
                    SELECT m.movie_id, m.movie_name, m.year, m.imdb_rating, mg.genre_id
                    FROM movies m
                    JOIN movie_genres mg ON m.movie_id = mg.movie_id
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM watched_movies wm
                        WHERE wm.user_id = :user_id
                          AND wm.movie_id = m.movie_id
                    )
                )
                SELECT
                    um.movie_id,
                    um.movie_name,
                    um.year,
                    um.imdb_rating,
                    MAX(g.genre_name) AS genre_name,
                    MAX(ugp.avg_genre_rating) AS predicted_rating
                FROM unwatched_movies um
                JOIN user_genre_preferences ugp ON um.genre_id = ugp.genre_id
                JOIN genres g ON g.genre_id = um.genre_id
                GROUP BY um.movie_id, um.movie_name, um.year, um.imdb_rating
                ORDER BY MAX(ugp.avg_genre_rating) DESC, um.imdb_rating DESC
                LIMIT 5
                """
            ),
            {"user_id": user_id}
        ).mappings().all()

    return {
        "description": "Your Top 5 Recommended Movies",
        "collection": [
            {
                "movie_id": rec["movie_id"],
                "movie_name": rec["movie_name"],
                "release_year": rec["year"],
                "imdb_rating": decimal_to_float(rec["imdb_rating"]),
                "genre": rec["genre_name"],
                "predicted_rating": decimal_to_float(rec["predicted_rating"]),
            }
            for rec in recs
        ]
    }

@router.get("/{user_id}/insights", tags=["collection"])
def get_user_insights(user_id: int):
    with db.engine.begin() as connection:
        favorite_genres = connection.execute(
            sqlalchemy.text(
                """
                SELECT g.genre_name, COUNT(*) AS watch_count
                FROM watched_movies wm
                JOIN movie_genres mg ON wm.movie_id = mg.movie_id
                JOIN genres g ON mg.genre_id = g.genre_id
                WHERE wm.user_id = :user_id AND wm.watch_status = TRUE
                GROUP BY g.genre_id, g.genre_name
                ORDER BY watch_count DESC
                LIMIT 3;
                """
            ),
            {"user_id": user_id}
        ).mappings().all()

        top_director = connection.execute(
           sqlalchemy.text(
                """
                SELECT d.name, COUNT(*) AS watch_count
                FROM watched_movies wm
                JOIN movie_directors md ON wm.movie_id = md.movie_id
                JOIN directors d ON md.director_id = d.director_id
                WHERE wm.user_id = :user_id AND wm.watch_status = TRUE
                GROUP BY d.director_id, d.name
                ORDER BY watch_count DESC
                """
            ),
            {"user_id": user_id}
        ).mappings().first()

        top_actor = connection.execute(
           sqlalchemy.text(
                """
                SELECT a.actor_name, COUNT(*) AS watch_count
                FROM watched_movies wm
                JOIN movie_actors ma ON wm.movie_id = ma.movie_id
                JOIN actors a ON ma.actor_id = a.actor_id
                WHERE wm.user_id = :user_id AND wm.watch_status = TRUE
                GROUP BY a.actor_id, a.actor_name
                ORDER BY watch_count DESC
                """
            ),
            {"user_id": user_id}
        ).mappings().first()

        top_decades = connection.execute(
            sqlalchemy.text(
                """
                SELECT CONCAT((m.year / 10) * 10, 's') AS decade, COUNT(*) AS watch_count
                FROM watched_movies wm
                JOIN movies m ON wm.movie_id = m.movie_id
                WHERE wm.user_id = :user_id AND wm.watch_status = TRUE AND m.year IS NOT NULL
                GROUP BY (m.year / 10) * 10
                ORDER BY watch_count DESC
                LIMIT 3
                """
            ),
            {"user_id": user_id}
        ).mappings().all()

        return {
            "favorite_genres": [genre["genre_name"] for genre in favorite_genres],
            "top_director": top_director,
            "top_actor": top_actor,
            "top_decade": [decade["decade"] for decade in top_decades]
        }