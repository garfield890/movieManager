import csv
import os
from decimal import Decimal, InvalidOperation

import psycopg
from dotenv import load_dotenv


BASICS_PATH = "imdb_data/title.basics.tsv"
RATINGS_PATH = "imdb_data/title.ratings.tsv"
BATCH_SIZE = 5000


def clean_int(value: str | None) -> int | None:
    if value is None or value == r"\N" or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def clean_rating(value: str | None) -> Decimal | None:
    if value is None or value == r"\N" or value == "":
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def load_ratings() -> dict[str, Decimal]:
    ratings: dict[str, Decimal] = {}

    with open(RATINGS_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            rating = clean_rating(row.get("averageRating"))
            if rating is not None:
                ratings[row["tconst"]] = rating

    return ratings


def flush_movies(conn: psycopg.Connection, rows: list[tuple]) -> None:
    if not rows:
        return

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO movies (
                movie_name,
                year,
                imdb_rating,
                runtime,
                mpaa_rating,
                plot
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT uq_movies_name_year DO NOTHING
            """,
            rows,
        )

    conn.commit()
    rows.clear()


def main() -> None:
    load_dotenv()

    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        raise RuntimeError("POSTGRES_URI is not set")

    print("Loading IMDb ratings into memory...")
    ratings = load_ratings()
    print(f"Loaded {len(ratings):,} ratings")

    conn = psycopg.connect(postgres_uri)

    inserted_candidates = 0
    batch: list[tuple] = []

    try:
        with open(BASICS_PATH, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")

            for row in reader:
                if row.get("titleType") != "movie":
                    continue

                movie_name = row.get("primaryTitle")
                if not movie_name or movie_name == r"\N":
                    continue

                year = clean_int(row.get("startYear"))
                runtime = clean_int(row.get("runtimeMinutes"))
                if runtime is None:
                    runtime = 0
                imdb_rating = ratings.get(row["tconst"])
                batch.append(
                    (
                        movie_name,
                        year,
                        imdb_rating,
                        runtime,
                        "UNKNOWN",
                        "",
                    )
                )

                inserted_candidates += 1

                if len(batch) >= BATCH_SIZE:
                    flush_movies(conn, batch)
                    print(f"Processed {inserted_candidates:,} movie rows...")

        flush_movies(conn, batch)
        print(f"Done. Processed {inserted_candidates:,} movie rows.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()