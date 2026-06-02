import csv
import os
from collections.abc import Iterable

import psycopg
from dotenv import load_dotenv


BASICS_PATH = "imdb_data/title.basics.tsv"
CREW_PATH = "imdb_data/title.crew.tsv"
NAMES_PATH = "imdb_data/name.basics.tsv"
BATCH_SIZE = 5000


def clean_int(value: str | None) -> int | None:
    if value is None or value == r"\N" or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_imdb_list(value: str | None) -> list[str]:
    if value is None or value == r"\N" or value == "":
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


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
    cur.execute(
        """
        SELECT movie_id, movie_name, year
        FROM movies
        """
    )

    return {
        (movie_name, year): movie_id
        for movie_id, movie_name, year in cur.fetchall()
    }


def load_tconst_to_movie_id(
    movie_map: dict[tuple[str, int | None], int]
) -> dict[str, int]:
    tconst_to_movie_id: dict[str, int] = {}

    matched = 0
    skipped = 0

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
                skipped += 1
                continue

            tconst_to_movie_id[row["tconst"]] = movie_id
            matched += 1

            if matched % 50_000 == 0:
                print(
                    f"Matched {matched:,} IMDb titles to local movies; "
                    f"skipped {skipped:,}"
                )

    return tconst_to_movie_id


def collect_needed_director_nconsts(
    tconst_to_movie_id: dict[str, int]
) -> set[str]:
    needed: set[str] = set()

    with open(CREW_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            tconst = row.get("tconst")
            if tconst not in tconst_to_movie_id:
                continue

            for director_nconst in parse_imdb_list(row.get("directors")):
                needed.add(director_nconst)

    return needed


def load_director_names(
    needed_director_nconsts: set[str],
) -> dict[str, str]:
    director_name_by_nconst: dict[str, str] = {}

    scanned = 0

    with open(NAMES_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            scanned += 1
            nconst = row.get("nconst")

            if nconst in needed_director_nconsts:
                primary_name = row.get("primaryName")
                if primary_name and primary_name != r"\N":
                    director_name_by_nconst[nconst] = primary_name

            if scanned % 500_000 == 0:
                print(
                    f"Scanned {scanned:,} names; "
                    f"loaded {len(director_name_by_nconst):,}/"
                    f"{len(needed_director_nconsts):,} directors"
                )

            if len(director_name_by_nconst) == len(needed_director_nconsts):
                break

    return director_name_by_nconst


def load_director_id_by_name(cur: psycopg.Cursor) -> dict[str, int]:
    cur.execute(
        """
        SELECT director_id, name
        FROM directors
        """
    )

    return {
        name: director_id
        for director_id, name in cur.fetchall()
    }


def generate_movie_director_pairs(
    tconst_to_movie_id: dict[str, int],
    director_name_by_nconst: dict[str, str],
    director_id_by_name: dict[str, int],
) -> Iterable[tuple[int, int]]:
    seen_pairs: set[tuple[int, int]] = set()

    processed = 0

    with open(CREW_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            tconst = row.get("tconst")
            movie_id = tconst_to_movie_id.get(tconst)

            if movie_id is None:
                continue

            director_nconsts = parse_imdb_list(row.get("directors"))
            if not director_nconsts:
                continue

            for director_nconst in director_nconsts:
                director_name = director_name_by_nconst.get(director_nconst)
                if director_name is None:
                    continue

                director_id = director_id_by_name.get(director_name)
                if director_id is None:
                    continue

                pair = (movie_id, director_id)
                if pair in seen_pairs:
                    continue

                seen_pairs.add(pair)
                yield pair

            processed += 1
            if processed % 50_000 == 0:
                print(f"Processed directors for {processed:,} matched movies...")


def main() -> None:
    load_dotenv()

    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        raise RuntimeError("POSTGRES_URI is not set")

    conn = psycopg.connect(postgres_uri)

    try:
        with conn.cursor() as cur:
            print("Loading local movie map...")
            movie_map = load_movie_map(cur)
            print(f"Loaded {len(movie_map):,} movies from local DB")

            print("Matching IMDb tconst to local movie_id...")
            tconst_to_movie_id = load_tconst_to_movie_id(movie_map)
            print(f"Matched {len(tconst_to_movie_id):,} IMDb titles")

            print("Collecting director nconsts from title.crew.tsv...")
            needed_director_nconsts = collect_needed_director_nconsts(
                tconst_to_movie_id
            )
            print(f"Needed director nconsts: {len(needed_director_nconsts):,}")

            print("Loading director names from name.basics.tsv...")
            director_name_by_nconst = load_director_names(needed_director_nconsts)
            print(f"Loaded director names: {len(director_name_by_nconst):,}")

            print("Inserting directors...")
            director_rows = [
                (name,)
                for name in sorted(set(director_name_by_nconst.values()))
            ]

            attempted_director_inserts = insert_batches(
                cur,
                """
                INSERT INTO directors (name)
                VALUES (%s)
                ON CONFLICT (name) DO NOTHING
                """,
                director_rows,
            )
            conn.commit()
            print(f"Attempted director inserts: {attempted_director_inserts:,}")

            print("Loading director IDs from database...")
            director_id_by_name = load_director_id_by_name(cur)
            print(f"Loaded director IDs: {len(director_id_by_name):,}")

            print("Generating and inserting movie_directors...")
            movie_director_pairs = generate_movie_director_pairs(
                tconst_to_movie_id,
                director_name_by_nconst,
                director_id_by_name,
            )

            attempted_pair_inserts = insert_batches(
                cur,
                """
                INSERT INTO movie_directors (movie_id, director_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                movie_director_pairs,
            )
            conn.commit()
            print(f"Attempted movie_directors inserts: {attempted_pair_inserts:,}")

            print("\nFinal counts:")
            cur.execute("SELECT COUNT(*) FROM directors")
            print(f"directors: {cur.fetchone()[0]:,}")

            cur.execute("SELECT COUNT(*) FROM movie_directors")
            print(f"movie_directors: {cur.fetchone()[0]:,}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()