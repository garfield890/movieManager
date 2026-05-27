from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr
from typing import Literal
from src.misc import GENRE_ALIASES, decimal_to_float
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import secrets

import sqlalchemy
from src.api import auth
from src import database as db

router = APIRouter(
    prefix="/users",
    dependencies=[Depends(auth.get_api_key)],
)

ph = PasswordHasher()

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=24)

class LoginRequest(BaseModel):
    username: str
    password: str

class AddCollectionRequest(BaseModel):
    watched: bool = True

class AddMovieByTitleRequest(BaseModel):
    title: str
    year: int
    watched: bool = True
    
class UpdateCollectionRequest(BaseModel):
    watched: bool = True
    rating: float | None = Field(default=0.0, ge=0, le=10)

class RegisterResponse(BaseModel):
    user_id: int
    username: str

class LoginResponse(BaseModel):
    user_id: int
    username: str
    token: str

class CollectionEntryResponse(BaseModel):
    movie_id: int
    title: str
    release_year: int | None
    imdb_rating: float | None
    runtime: int | None
    mpaa_rating: str | None
    plot: str | None
    watched: bool
    rating: float | None

class CollectionResponse(BaseModel):
    collection: list[CollectionEntryResponse]

class FilterRequest(BaseModel):
    genre: str = ""
    release_year: int = 0
    rating: float = -1.0
    director: str = ""
    actor: str = ""

class FilterEntryResponse(BaseModel):
    movie_id: int
    title: str
    release_year: int | None
    rating: float | None
    genre: str
    director: str
    actor: str | None = None

class FilterResponse(BaseModel):
    collection: list[FilterEntryResponse]

class RecommendationEntryResponse(BaseModel):
    movie_id: int
    title: str
    release_year: int | None
    imdb_rating: float | None
    runtime: int | None
    mpaa_rating: str | None
    plot: str | None
    genre: str | None = None
    predicted_rating: float | None = None
    reason: str | None = None

class RecommendationsResponse(BaseModel):
    description: str
    collection: list[RecommendationEntryResponse]

class InsightsLimits(BaseModel):
    genre_limit: int = Field(default=3, le=5)
    director_limit: int = Field(default=3, le=5)
    actor_limit: int = Field(default=3, le=5)
    decade_limit: int = Field(default=3, le=5)

class TopDirectorResponse(BaseModel):
    name: str
    watch_count: int

class TopActorResponse(BaseModel):
    actor_name: str
    watch_count: int

class InsightsResponse(BaseModel):
    favorite_genres: list[str]
    top_director: list[TopDirectorResponse] | None
    top_actor: list[TopActorResponse] | None
    top_decade: list[str]

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

@router.post("/register", tags=["users"], response_model=RegisterResponse)
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
        
        hashed_password = ph.hash(request.password)

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
                "password": hashed_password,
            },
        ).mappings().one()

    return {
        "user_id": row["user_id"],
        "username": row["username"],
    }


@router.post("/login", tags=["users"], response_model=LoginResponse)
def login_user(request: LoginRequest):
    with db.engine.begin() as conn:
        row = conn.execute(
            sqlalchemy.text(
                """
                SELECT user_id, username, password
                FROM users
                WHERE username = :username
                """
            ),
            {
                "username": request.username,
            },
        ).mappings().first()

        if row is None:
            raise HTTPException(status_code=401, detail="Invalid username")
        
        try:
            ph.verify(row["password"], request.password)
        except VerifyMismatchError:
            raise HTTPException(status_code=401, detail="Invalid password!")
        
        random_part = secrets.token_urlsafe(12)[:16]
        token = f"login-token-{row['user_id']}-{random_part}" 

        conn.execute(
            sqlalchemy.text(
                """
                INSERT INTO logins (user_id, login_token)
                VALUES (:user_id, :token)
                ON CONFLICT (user_id) DO UPDATE
                SET login_token = EXCLUDED.login_token
                """
            ),
            {
                "user_id": row["user_id"],
                "token": token
            }
        )

        return {
            "user_id": row["user_id"],
            "username": row["username"],
            "token": token,
        }

@router.post("/{login_token}/collection/add_by_title", tags=["collection"])
def add_movie_to_collection_by_title(login_token: str, request: AddMovieByTitleRequest):
    with db.engine.begin() as connection:
        user = connection.execute(
            sqlalchemy.text(
                """
                SELECT users.user_id
                FROM users
                JOIN logins ON logins.user_id = users.user_id
                WHERE login_token = :token
                """
            ),
            {"token": login_token},
        ).mappings().first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        movie = connection.execute(
            sqlalchemy.text(
                """
                SELECT movie_id, movie_name
                FROM movies
                WHERE movie_name = :title
                AND year = :year
                """
            ),
            {
                "title": request.title,
                "year": request.year,
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
                    """
                ),
                {"title": request.title},
            ).scalars().all()

            if other_years:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "message": f"No movie found for '{request.title}' in {request.year}.",
                        "available_years": other_years,
                    },
                )

            raise HTTPException(status_code=404, detail="Movie not found")

        row = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO watched_movies (user_id, movie_id, watched, rating)
                VALUES (:user_id, :movie_id, :watched, NULL)
                ON CONFLICT (user_id, movie_id) DO UPDATE
                SET watched = EXCLUDED.watched, updated_at = now()
                RETURNING user_id, movie_id, watched, rating
                """
            ),
            {
                "user_id": user["user_id"],
                "movie_id": movie["movie_id"],
                "watched": request.watched,
            },
        ).mappings().one()

    return {
        "user_id": row["user_id"],
        "movie_id": row["movie_id"],
        "title": movie["movie_name"],
        "watched": row["watched"],
        "rating": decimal_to_float(row["rating"]),
    }

@router.post("/{login_token}/collection/{movie_id}", tags=["collection"])
def add_movie_to_collection(
    login_token: str,
    movie_id: int,
    request: AddCollectionRequest,
):
    with db.engine.begin() as connection:
        user = connection.execute(
            sqlalchemy.text(
                """
                SELECT users.user_id
                FROM users
                JOIN logins ON logins.user_id = users.user_id
                WHERE login_token = :token
                """
            ),
            {"token": login_token},
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
                INSERT INTO watched_movies (user_id, movie_id, watched, rating)
                VALUES (:user_id, :movie_id, :watched, NULL)
                ON CONFLICT (user_id, movie_id) DO UPDATE
                SET watched = EXCLUDED.watched
                RETURNING user_id, movie_id, watched, rating
                """
            ),
            {
                "user_id": user["user_id"],
                "movie_id": movie_id,
                "watched": request.watched,
            },
        ).mappings().one()

    return {
        "user_id": row["user_id"],
        "movie_id": row["movie_id"],
        "watched": row["watched"],
        "rating": decimal_to_float(row["rating"]),
    }

@router.put("/{login_token}/collection/{movie_id}", tags=["collection"])
def update_movie_in_collection(
    login_token: str,
    movie_id: int,
    request: UpdateCollectionRequest,
):
    with db.engine.begin() as connection:
        user = connection.execute(
            sqlalchemy.text(
                """
                SELECT users.user_id
                FROM users
                JOIN logins ON logins.user_id = users.user_id
                WHERE login_token = :token
                """
            ),
            {"token": login_token},
        ).mappings().first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not request.watched and request.rating is not None:
            raise HTTPException(
                status_code=400,
                detail="Cannot rate a movie that has not been watched.",
        )
        
        row = connection.execute(
            sqlalchemy.text(
                """
                UPDATE watched_movies
                SET watched = :watched,
                    rating = :rating,
                    updated_at = now()
                WHERE user_id = :user_id
                AND movie_id = :movie_id
                RETURNING user_id, movie_id, watched, rating
                """
            ),
            {
                "user_id": user["user_id"],
                "movie_id": movie_id,
                "watched": request.watched,
                "rating": request.rating,
            },
        ).mappings().first()

        if row is None:
            raise HTTPException(status_code=404, detail="Collection entry not found")

    return {
        "user_id": row["user_id"],
        "movie_id": row["movie_id"],
        "watched": row["watched"],
        "rating": decimal_to_float(row["rating"]),
    }

@router.delete("/{login_token}/collection/{movie_id}", tags=["collection"])
def remove_movie_from_collection(
    login_token: str,
    movie_id: int, 
):
    with db.engine.begin() as connection:
        user = connection.execute(
            sqlalchemy.text(
                """
                SELECT users.user_id
                FROM users
                JOIN logins ON logins.user_id = users.user_id
                WHERE login_token = :token
                """
            ),
            {"token": login_token},
        ).mappings().first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
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

        deleted = connection.execute(
            sqlalchemy.text(
                """
                DELETE FROM watched_movies wm
                WHERE wm.movie_id = :movie_id AND wm.user_id = :user_id
                """
            ),
            {
                "user_id": user["user_id"],
                "movie_id": movie_id
            }
        ).first()
    
    if deleted is None:
        raise HTTPException(status_code=404, detail="Collection entry not found")

    return {
        "user_id": user["user_id"],
        "movie_name": movie_name,
        "removed": True
    }

@router.get("/{login_token}/collection", tags=["collection"], response_model=CollectionResponse)
def get_user_collection(login_token: str):
    with db.engine.begin() as connection:
        user = connection.execute(
            sqlalchemy.text(
                """
                SELECT users.user_id
                FROM users
                JOIN logins ON logins.user_id = users.user_id
                WHERE login_token = :token
                """
            ),
            {"token": login_token},
        ).mappings().first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        rows = connection.execute(
            sqlalchemy.text(
                """
                SELECT
                    m.movie_id,
                    m.movie_name,
                    m.year,
                    m.imdb_rating,
                    m.runtime,
                    m.mpaa_rating,
                    m.plot,
                    wm.watched,
                    wm.rating
                FROM watched_movies wm
                JOIN movies m ON wm.movie_id = m.movie_id
                WHERE wm.user_id = :user_id
                ORDER BY m.movie_name
                """
            ),
            {"user_id": user["user_id"]},
        ).mappings().all()

    return {
        "collection": [
            {
                "movie_id": row["movie_id"],
                "title": row["movie_name"],
                "release_year": row["year"],
                "imdb_rating": decimal_to_float(row["imdb_rating"]),
                "runtime": row["runtime"],
                "mpaa_rating": row["mpaa_rating"],
                "plot": row["plot"],
                "watched": row["watched"],
                "rating": decimal_to_float(row["rating"]),
            }
            for row in rows
        ]
    }

@router.get("/{login_token}/collection/filter", tags=["collection"], response_model=FilterResponse)
def filter_movie_collection(login_token: str, filters: FilterRequest = Depends()):
    with db.engine.begin() as connection:
        user = connection.execute(
            sqlalchemy.text(
                """
                SELECT users.user_id
                FROM users
                JOIN logins ON logins.user_id = users.user_id
                WHERE login_token = :token
                """
            ),
            {"token": login_token},
        ).mappings().first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        genre = filters.genre
        if filters.genre != "":
            genre = GENRE_ALIASES.get(filters.genre, filters.genre)
        
        result = connection.execute(
            sqlalchemy.text(
                """
                SELECT DISTINCT ON (movies.movie_id) movies.movie_id, movies.movie_name, movies.year AS movie_year, wm.rating, g.genre_name, d.name AS director_name, a.actor_name
                FROM watched_movies wm
                JOIN movies ON wm.movie_id = movies.movie_id
                JOIN movie_genres mg ON mg.movie_id = movies.movie_id
                JOIN genres g ON g.genre_id = mg.genre_id
                JOIN movie_directors md ON md.movie_id = movies.movie_id
                JOIN directors d ON d.director_id = md.director_id
                JOIN movie_actors ma ON ma.movie_id = movies.movie_id
                JOIN actors a ON a.actor_id = ma.actor_id
                WHERE wm.user_id = :user_id AND (:genre = '' OR g.genre_name = :genre) AND (:director = '' OR d.name = :director) AND (:actor = '' OR a.actor_name = :actor) AND (:release_year = 0 OR movies.year = :release_year) AND (:rating = -1.0 OR wm.rating = :rating) AND wm.watched = True
                ORDER BY movies.movie_id, wm.rating DESC NULLS LAST
                """
            ),
            {
                "user_id": user["user_id"],
                "genre": genre,
                "director": filters.director,
                "actor": filters.actor,
                "release_year": filters.release_year,
                "rating": filters.rating,
            }
        ).mappings().all()

        return {
            "collection": [
                {
                    "movie_id": row["movie_id"],
                    "title": row["movie_name"],
                    "release_year": row["movie_year"],
                    "rating": decimal_to_float(row["rating"]),
                    "genre": row["genre_name"],
                    "director": row["director_name"],
                    **({"actor": row["actor_name"]} if filters.actor != "" else {}),
                }
                for row in result
            ]
        }

@router.get("/{login_token}/recommendations", tags=["users"], response_model=RecommendationsResponse)
def recommend_movies(login_token: str):
    with db.engine.begin() as connection:
        user = connection.execute(
            sqlalchemy.text(
                """
                SELECT users.user_id
                FROM users
                JOIN logins ON logins.user_id = users.user_id
                WHERE login_token = :token
                """
            ),
            {"token": login_token},
        ).mappings().first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        top_unwatched = connection.execute(
            sqlalchemy.text(
                """
                SELECT DISTINCT ON (g.genre_name)
                    m.movie_id, m.movie_name, m.year, m.imdb_rating, m.runtime, m.mpaa_rating, m.plot, g.genre_name
                FROM movies m
                JOIN movie_genres mg ON m.movie_id = mg.movie_id
                JOIN genres g ON mg.genre_id = g.genre_id
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM watched_movies wm
                    WHERE wm.user_id = :user_id
                      AND wm.movie_id = m.movie_id
                )
                ORDER BY g.genre_name, m.imdb_rating DESC NULLS LAST
                LIMIT 5
                """
            ),
            {"user_id": user["user_id"]}
        ).mappings().all()

        watched_movies = connection.execute(
            sqlalchemy.text(
                """
                SELECT COUNT(*)
                FROM watched_movies wm
                WHERE wm.user_id = :user_id
                """
            ),
            { "user_id": user["user_id"]}
        ).scalar_one()

        top_genre = connection.execute(
            sqlalchemy.text(
                """
                SELECT g.genre_name
                FROM watched_movies wm
                JOIN movie_genres mg ON wm.movie_id = mg.movie_id
                JOIN genres g ON mg.genre_id = g.genre_id
                WHERE wm.user_id = :user_id
                  AND wm.rating IS NOT NULL
                GROUP BY g.genre_id, g.genre_name
                ORDER BY AVG(wm.rating) DESC, COUNT(*) DESC, g.genre_name
                LIMIT 1
                """
            ),
            {"user_id": user["user_id"]},
        ).scalar_one_or_none()

        top_director = connection.execute(
            sqlalchemy.text(
                """
                SELECT d.name
                FROM watched_movies wm
                JOIN movie_directors md ON wm.movie_id = md.movie_id
                JOIN directors d ON md.director_id = d.director_id
                WHERE wm.user_id = :user_id
                  AND wm.watched = TRUE
                GROUP BY d.director_id, d.name
                ORDER BY COUNT(*) DESC, d.name
                LIMIT 1
                """
            ),
            {"user_id": user["user_id"]},
        ).scalar_one_or_none()

        if watched_movies < 5:
            return {
                "description": "Not enough movies watched to provide personalized recommendations. Here are the top unwatched movies across 5 genres.",
                "collection": [
                    {
                        "movie_id": row["movie_id"],
                        "title": row["movie_name"],
                        "release_year": row["year"],
                        "imdb_rating": decimal_to_float(row["imdb_rating"]),
                        "runtime": row["runtime"],
                        "mpaa_rating": row["mpaa_rating"],
                        "plot": row["plot"],
                        "genre": row["genre_name"],
                        "reason": f"Top rated unwatched movie in {row['genre_name']}.",
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
                    SELECT m.movie_id, m.movie_name, m.year, m.imdb_rating, m.runtime, m.mpaa_rating, m.plot, mg.genre_id
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
                    MAX(um.runtime) AS runtime,
                    MAX(um.mpaa_rating) AS mpaa_rating,
                    MAX(um.plot) AS plot,
                    MAX(g.genre_name) AS genre_name,
                    MAX(d.name) AS director_name,
                    ROUND(MAX(ugp.avg_genre_rating), 2) AS predicted_rating
                FROM unwatched_movies um
                JOIN user_genre_preferences ugp ON um.genre_id = ugp.genre_id
                JOIN genres g ON g.genre_id = um.genre_id
                JOIN movie_directors md ON md.movie_id = um.movie_id
                JOIN directors d ON d.director_id = md.director_id
                GROUP BY um.movie_id, um.movie_name, um.year, um.imdb_rating
                ORDER BY MAX(ugp.avg_genre_rating) DESC, um.imdb_rating DESC
                LIMIT 5
                """
            ),
            {"user_id": user["user_id"]}
        ).mappings().all()

    return {
        "description": "Your Top 5 Recommended Movies",
        "collection": [
            {
                "movie_id": rec["movie_id"],
                "title": rec["movie_name"],
                "release_year": rec["year"],
                "imdb_rating": decimal_to_float(rec["imdb_rating"]),
                "runtime": rec["runtime"],
                "mpaa_rating": rec["mpaa_rating"],
                "plot": rec["plot"],
                "genre": rec["genre_name"],
                "predicted_rating": decimal_to_float(rec["predicted_rating"]),
                "reason": (
                    f"Because you rate {rec['genre_name']} movies highly and often watch {rec['director_name']} movies."
                    if top_genre == rec["genre_name"] and top_director == rec["director_name"]
                    else f"Because you rate {rec['genre_name']} movies highly."
                    if top_genre == rec["genre_name"]
                    else f"Because you often watch {rec['director_name']} movies."
                    if top_director == rec["director_name"]
                    else "Because it matches your watch history and preferences."
                ),
            }
            for rec in recs
        ]
    }

@router.get("/{login_token}/insights", tags=["users"], response_model=InsightsResponse)
def get_user_insights(login_token: str, limits: InsightsLimits = Depends()):
    with db.engine.begin() as connection:
        user = connection.execute(
            sqlalchemy.text(
                """
                SELECT users.user_id
                FROM users
                JOIN logins ON logins.user_id = users.user_id
                WHERE login_token = :token
                """
            ),
            {"token": login_token},
        ).mappings().first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        favorite_genres = connection.execute(
            sqlalchemy.text(
                """
                SELECT g.genre_name, COUNT(*) AS watch_count
                FROM watched_movies wm
                JOIN movie_genres mg ON wm.movie_id = mg.movie_id
                JOIN genres g ON mg.genre_id = g.genre_id
                WHERE wm.user_id = :user_id AND wm.watched = TRUE
                GROUP BY g.genre_id, g.genre_name
                ORDER BY watch_count DESC
                LIMIT :genre_limit;
                """
            ),
            {
                "user_id": user["user_id"], 
                "genre_limit": limits.genre_limit
            }
        ).mappings().all()

        top_director = connection.execute(
           sqlalchemy.text(
                """
                SELECT d.name, COUNT(*) AS watch_count
                FROM watched_movies wm
                JOIN movie_directors md ON wm.movie_id = md.movie_id
                JOIN directors d ON md.director_id = d.director_id
                WHERE wm.user_id = :user_id AND wm.watched = TRUE
                GROUP BY d.director_id, d.name
                ORDER BY watch_count DESC
                LIMIT :director_limit;
                """
            ),
            {
                "user_id": user["user_id"],
                "director_limit": limits.director_limit
            }
        ).mappings().all()

        top_actor = connection.execute(
           sqlalchemy.text(
                """
                SELECT a.actor_name, COUNT(*) AS watch_count
                FROM watched_movies wm
                JOIN movie_actors ma ON wm.movie_id = ma.movie_id
                JOIN actors a ON ma.actor_id = a.actor_id
                WHERE wm.user_id = :user_id AND wm.watched = TRUE
                GROUP BY a.actor_id, a.actor_name
                ORDER BY watch_count DESC
                LIMIT :actor_limit
                """
            ),
            {
                "user_id": user["user_id"],
                "actor_limit": limits.actor_limit
            }
        ).mappings().all()

        top_decades = connection.execute(
            sqlalchemy.text(
                """
                SELECT CONCAT((m.year / 10) * 10, 's') AS decade, COUNT(*) AS watch_count
                FROM watched_movies wm
                JOIN movies m ON wm.movie_id = m.movie_id
                WHERE wm.user_id = :user_id AND wm.watched = TRUE AND m.year IS NOT NULL
                GROUP BY (m.year / 10) * 10
                ORDER BY watch_count DESC
                LIMIT :decade_limit;
                """
            ),
            {
                "user_id": user["user_id"],
                "decade_limit": limits.decade_limit
            }
        ).mappings().all()

        return {
            "favorite_genres": [genre["genre_name"] for genre in favorite_genres],
            "top_director": [{"name": d["name"], "watch_count": d["watch_count"]} for d in top_director] if top_director else None,
            "top_actor": [{"actor_name": a["actor_name"], "watch_count": a["watch_count"]} for a in top_actor] if top_actor else None,
            "top_decade": [decade["decade"] for decade in top_decades]
        }


LEADERBOARD_SORT_COLUMNS = {
    "movies_watched": "COUNT(*)",
    "hours_watched": "COALESCE(SUM(m.runtime), 0) / 60.0",
    "average_rating": "ROUND(AVG(wm.rating)::numeric, 2)",
    "movies_rated": "COUNT(wm.rating)",
    "highest_rated_movie": "MAX(wm.rating)",
}

@router.get("/leaderboard/{genre}/{limit}", tags=["users"], response_model=LeaderboardResponse)
def get_leaderboard(
    genre: str, 
    limit: int, 
    sort_by: Literal["movies_watched", "hours_watched", "average_rating", "movies_rated", "highest_rated_movie"] = Query(default="movies_watched")
):
    order_col = LEADERBOARD_SORT_COLUMNS[sort_by]
    genre = GENRE_ALIASES.get(genre, '')

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
