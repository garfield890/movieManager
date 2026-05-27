#Erlin Zhao
from pathlib import Path
import json
import sqlalchemy
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ["POSTGRES_URI"]
engine = sqlalchemy.create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)
DATA_FILE = Path("sample_movies/movies-250.json")
def parse_movies(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    movies = data.get("movies", [])

    parsed_movies = []
    for movie in movies:
        title = movie.get("Title")
        year = movie.get("Year")
        director = movie.get("Director")
        genre = movie.get("Genre")
        imdb_rating = movie.get("imdbRating")
        actors = movie.get("Actors")
        runtime = movie.get("Runtime")
        mpaa_rating = movie.get("Rated")
        plot = movie.get("Plot")
        parsed_movie = {
            "title": title,
            "year": year,
            "director": director,
            "genre": genre,
            "imdb_rating": imdb_rating,
            "actors": actors,
            "runtime": runtime,
            "mpaa_rating": mpaa_rating,
            "plot": plot,
        }

        parsed_movies.append(parsed_movie)
    return parsed_movies

#ensure value is str 
def clean(value):
    if value is None:
        return None
    value = str(value).strip()
    return value
#year must be 4 digit int
def parse_year(value):
    value = clean(value)
    if value is None:
        return None
    try:
        return int(value[:4])
    except ValueError:
        return None
#rating must be float between 0 and 10
def parse_rating(value):
    value = clean(value)

    if value is None:
        return None

    try:
        rating = float(value)
        if 0 <= rating <= 10:
            return rating
    except ValueError:
        return None

def split_list(value):
    value = clean(value)
    if value is None:
        return []
    result = []
    for item in value.split(","):
        item = item.strip()
        if item:
            result.append(item)
    return result

def parse_runtime(value):
    value = clean(value)
    if value is None:
        return None
    try:
        return int(value.replace("min", "").strip())
    except ValueError:
        return None

def upload_movie(connection, movie):
    result = connection.execute(
        sqlalchemy.text(
            """
            INSERT INTO movies (movie_name, year, imdb_rating, runtime, mpaa_rating, plot)
            VALUES (:movie_name, :year, :imdb_rating, :runtime, :mpaa_rating, :plot)
            ON CONFLICT (movie_name, year) DO UPDATE
            SET imdb_rating = EXCLUDED.imdb_rating,
                runtime = EXCLUDED.runtime,
                mpaa_rating = EXCLUDED.mpaa_rating,
                plot = EXCLUDED.plot
            RETURNING movie_id
            """
        ),
        {
            "movie_name": clean(movie["title"]),
            "year": parse_year(movie["year"]),
            "imdb_rating": parse_rating(movie["imdb_rating"]),
            "runtime": parse_runtime(movie["runtime"]),
            "mpaa_rating": clean(movie["mpaa_rating"]),
            "plot": clean(movie["plot"]),
        },
    )

    return result.scalar_one()
def upsert_director(connection, name):
    result = connection.execute(
        sqlalchemy.text(
            """
            INSERT INTO directors (name)
            VALUES (:name)
            ON CONFLICT (name) DO UPDATE
            SET name = EXCLUDED.name
            RETURNING director_id
            """
        ),
        {"name": name},
    )
    return result.scalar_one()

def upsert_actor(connection, actor_name):
    result = connection.execute(
        sqlalchemy.text(
            """
            INSERT INTO actors (actor_name)
            VALUES (:actor_name)
            ON CONFLICT (actor_name) DO UPDATE
            SET actor_name = EXCLUDED.actor_name
            RETURNING actor_id
            """
        ),
        {"actor_name": actor_name},
    )
    return result.scalar_one()
def upsert_genre(connection, genre_name):
    result = connection.execute(
        sqlalchemy.text(
            """
            INSERT INTO genres (genre_name)
            VALUES (:genre_name)
            ON CONFLICT (genre_name) DO UPDATE
            SET genre_name = EXCLUDED.genre_name
            RETURNING genre_id
            """
        ),
        {"genre_name": genre_name},
    )

    return result.scalar_one()
def link_movie_director(connection, movie_id, director_id):
    connection.execute(
        sqlalchemy.text(
            """
            INSERT INTO movie_directors (movie_id, director_id)
            VALUES (:movie_id, :director_id)
            ON CONFLICT DO NOTHING
            """
        ),
        {"movie_id": movie_id, "director_id": director_id},
    )

def link_movie_actor(connection, movie_id, actor_id):
    connection.execute(
        sqlalchemy.text(
            """
            INSERT INTO movie_actors (movie_id, actor_id)
            VALUES (:movie_id, :actor_id)
            ON CONFLICT DO NOTHING
            """
        ),
        {"movie_id": movie_id, "actor_id": actor_id},
    )


def link_movie_genre(connection, movie_id, genre_id):
    connection.execute(
        sqlalchemy.text(
            """
            INSERT INTO movie_genres (movie_id, genre_id)
            VALUES (:movie_id, :genre_id)
            ON CONFLICT DO NOTHING
            """
        ),
        {"movie_id": movie_id, "genre_id": genre_id},
    )

def main():
    movies = parse_movies(DATA_FILE)
    count = 0
    with engine.begin() as connection:
        for movie in movies:
            title = clean(movie["title"])

            if title is None:
                continue

            movie_id = upload_movie(connection, movie)

            for director_name in split_list(movie["director"]):
                director_id = upsert_director(connection, director_name)
                link_movie_director(connection, movie_id, director_id)

            for actor_name in split_list(movie["actors"]):
                actor_id = upsert_actor(connection, actor_name)
                link_movie_actor(connection, movie_id, actor_id)

            for genre_name in split_list(movie["genre"]):
                genre_id = upsert_genre(connection, genre_name)
                link_movie_genre(connection, movie_id, genre_id)

            count += 1
            print(f"Seeded {count} movies.")
    print(f"Seeded {count} movies.")


if __name__ == "__main__":
    main()