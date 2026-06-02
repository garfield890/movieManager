import csv
import os
from collections.abc import Iterable

import psycopg
from dotenv import load_dotenv
BASICS_PATH = "imdb_data/title.basics.tsv"
BATCH_SIZE = 5000
def clean_int(value: str | None) -> int | None:
    if value is None or value == r"\N" or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_genres(value: str | None) -> list[str]:
    if value is None or value == r"\N" or value == "":
        return []

    return [genre.strip() for genre in value.split(",") if genre.strip()]


def insert_batches(
    cur: psycopg.Cursor,
    sql: str,
    rows: Iterable[tuple],
    batch_size: int = BATCH_SIZE,
) -> int:
    batch = []
    total = 0

    for row in rows:
        batch.append(row)

        if len(batch) >= batch_size:
            cur.executemany(sql, batch)
            total += len(batch)
            batch.clear()

    if batch:
        cur.executemany(sql, batch)
        total += len(batch)

    return total


def load_movie_map(cur: psycopg.Cursor) -> dict[tuple[str, int | None], int]:
    """
    Map existing movies by (movie_name, year) -> movie_id.
    This matches how the current schema identifies movie uniqueness.
    """
    cur.execute(
        """
        SELECT movie_id, movie_name, year
        FROM movies
        """
    )

    movie_map: dict[tuple[str, int | None], int] = {}

    for movie_id, movie_name, year in cur.fetchall():
        movie_map[(movie_name, year)] = movie_id

    return movie_map


def collect_real_genres() -> set[str]:
    genres: set[str] = set()

    with open(BASICS_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            if row.get("titleType") != "movie":
                continue

            for genre in parse_genres(row.get("genres")):
                genres.add(genre)

    return genres


def load_genre_map(cur: psycopg.Cursor) -> dict[str, int]:
    cur.execute(
        """
        SELECT genre_id, genre_name
        FROM genres
        """
    )

    return {genre_name: genre_id for genre_id, genre_name in cur.fetchall()}


def generate_movie_genre_pairs(
    movie_map: dict[tuple[str, int | None], int],
    genre_map: dict[str, int],
) -> Iterable[tuple[int, int]]:
    seen_pairs: set[tuple[int, int]] = set()
    matched_movies = 0
    skipped_movies = 0

    with open(BASICS_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            if row.get("titleType") != "movie":
                continue

            movie_name = row.get("primaryTitle")
            if not movie_name or movie_name == r"\N":
                continue

            year = clean_int(row.get("startYear"))
            movie_id = movie_map.get((movie_name, year))

            if movie_id is None:
                skipped_movies += 1
                continue

            genres = parse_genres(row.get("genres"))
            if not genres:
                continue

            matched_movies += 1

            for genre in genres:
                genre_id = genre_map.get(genre)
                if genre_id is None:
                    continue

                pair = (movie_id, genre_id)
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    yield pair

            if matched_movies % 50_000 == 0:
                print(
                    f"Matched {matched_movies:,} movies; "
                    f"skipped {skipped_movies:,} unmatched IMDb rows..."
                )


def main() -> None:
    load_dotenv()

    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        raise RuntimeError("POSTGRES_URI is not set")

    conn = psycopg.connect(postgres_uri)

    try:
        with conn.cursor() as cur:
            print("Loading existing movies from database...")
            movie_map = load_movie_map(cur)
            print(f"Loaded {len(movie_map):,} movie keys")

            print("Collecting real IMDb genres...")
            real_genres = collect_real_genres()
            print(f"Found real IMDb genres: {sorted(real_genres)}")

            print("Inserting genres...")
            genre_rows = [(genre,) for genre in sorted(real_genres)]

            inserted_genres = insert_batches(
                cur,
                """
                INSERT INTO genres (genre_name)
                VALUES (%s)
                ON CONFLICT (genre_name) DO NOTHING
                """,
                genre_rows,
            )
            conn.commit()
            print(f"Attempted genre inserts: {inserted_genres:,}")

            print("Loading genre IDs...")
            genre_map = load_genre_map(cur)
            print(f"Loaded {len(genre_map):,} genres from database")

            print("Generating and inserting movie_genres from IMDb...")
            movie_genre_pairs = generate_movie_genre_pairs(movie_map, genre_map)

            inserted_pairs = insert_batches(
                cur,
                """
                INSERT INTO movie_genres (movie_id, genre_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                movie_genre_pairs,
            )
            conn.commit()
            print(f"Attempted movie_genres inserts: {inserted_pairs:,}")

            print("\nFinal counts:")
            cur.execute("SELECT COUNT(*) FROM genres")
            print(f"genres: {cur.fetchone()[0]:,}")

            cur.execute("SELECT COUNT(*) FROM movie_genres")
            print(f"movie_genres: {cur.fetchone()[0]:,}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()