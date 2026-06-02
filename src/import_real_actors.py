import csv
import os
from collections.abc import Iterable

import psycopg
from dotenv import load_dotenv


BASICS_PATH = "imdb_data/title.basics.tsv"
PRINCIPALS_PATH = "imdb_data/title.principals.tsv"
NAMES_PATH = "imdb_data/name.basics.tsv"
BATCH_SIZE = 5000

ACTOR_CATEGORIES = {"actor", "actress"}


def clean_int(value: str | None) -> int | None:
    if value is None or value == r"\N" or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


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
    Current schema has no imdb_id/tconst, so we match by (movie_name, year).
    """
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
    """
    Match IMDb tconst to local movies.movie_id using title.basics primaryTitle + startYear.
    """
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


def collect_needed_actor_nconsts(
    tconst_to_movie_id: dict[str, int],
) -> set[str]:
    """
    Read title.principals.tsv and collect actor/actress nconsts only
    for movies that exist locally.
    """
    needed: set[str] = set()
    matched_rows = 0

    with open(PRINCIPALS_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            tconst = row.get("tconst")
            if tconst not in tconst_to_movie_id:
                continue

            category = row.get("category")
            if category not in ACTOR_CATEGORIES:
                continue

            nconst = row.get("nconst")
            if nconst and nconst != r"\N":
                needed.add(nconst)

            matched_rows += 1
            if matched_rows % 200_000 == 0:
                print(
                    f"Scanned {matched_rows:,} actor principal rows; "
                    f"needed actors so far: {len(needed):,}"
                )

    return needed


def load_actor_names(
    needed_actor_nconsts: set[str],
) -> dict[str, str]:
    """
    Map actor nconst -> primaryName from name.basics.tsv.
    """
    actor_name_by_nconst: dict[str, str] = {}
    scanned = 0

    with open(NAMES_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            scanned += 1
            nconst = row.get("nconst")

            if nconst in needed_actor_nconsts:
                primary_name = row.get("primaryName")
                if primary_name and primary_name != r"\N":
                    actor_name_by_nconst[nconst] = primary_name

            if scanned % 500_000 == 0:
                print(
                    f"Scanned {scanned:,} names; "
                    f"loaded {len(actor_name_by_nconst):,}/"
                    f"{len(needed_actor_nconsts):,} actors"
                )

            if len(actor_name_by_nconst) == len(needed_actor_nconsts):
                break

    return actor_name_by_nconst


def load_actor_id_by_name(cur: psycopg.Cursor) -> dict[str, int]:
    cur.execute(
        """
        SELECT actor_id, actor_name
        FROM actors
        """
    )

    return {
        actor_name: actor_id
        for actor_id, actor_name in cur.fetchall()
    }


def generate_movie_actor_pairs(
    tconst_to_movie_id: dict[str, int],
    actor_name_by_nconst: dict[str, str],
    actor_id_by_name: dict[str, int],
) -> Iterable[tuple[int, int]]:
    """
    Re-read title.principals.tsv and produce local (movie_id, actor_id) pairs.
    """
    seen_pairs: set[tuple[int, int]] = set()
    processed = 0

    with open(PRINCIPALS_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            tconst = row.get("tconst")
            movie_id = tconst_to_movie_id.get(tconst)

            if movie_id is None:
                continue

            category = row.get("category")
            if category not in ACTOR_CATEGORIES:
                continue

            nconst = row.get("nconst")
            if not nconst or nconst == r"\N":
                continue

            actor_name = actor_name_by_nconst.get(nconst)
            if actor_name is None:
                continue

            actor_id = actor_id_by_name.get(actor_name)
            if actor_id is None:
                continue

            pair = (movie_id, actor_id)
            if pair in seen_pairs:
                continue

            seen_pairs.add(pair)
            yield pair

            processed += 1
            if processed % 200_000 == 0:
                print(f"Generated {processed:,} movie_actor pairs...")


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

            print("Collecting actor/actress nconsts from title.principals.tsv...")
            needed_actor_nconsts = collect_needed_actor_nconsts(tconst_to_movie_id)
            print(f"Needed actor nconsts: {len(needed_actor_nconsts):,}")

            print("Loading actor names from name.basics.tsv...")
            actor_name_by_nconst = load_actor_names(needed_actor_nconsts)
            print(f"Loaded actor names: {len(actor_name_by_nconst):,}")

            print("Inserting actors...")
            actor_rows = [
                (name,)
                for name in sorted(set(actor_name_by_nconst.values()))
            ]

            attempted_actor_inserts = insert_batches(
                cur,
                """
                INSERT INTO actors (actor_name)
                VALUES (%s)
                ON CONFLICT (actor_name) DO NOTHING
                """,
                actor_rows,
            )
            conn.commit()
            print(f"Attempted actor inserts: {attempted_actor_inserts:,}")

            print("Loading actor IDs from database...")
            actor_id_by_name = load_actor_id_by_name(cur)
            print(f"Loaded actor IDs: {len(actor_id_by_name):,}")

            print("Generating and inserting movie_actors...")
            movie_actor_pairs = generate_movie_actor_pairs(
                tconst_to_movie_id,
                actor_name_by_nconst,
                actor_id_by_name,
            )

            attempted_pair_inserts = insert_batches(
                cur,
                """
                INSERT INTO movie_actors (movie_id, actor_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                movie_actor_pairs,
            )
            conn.commit()
            print(f"Attempted movie_actors inserts: {attempted_pair_inserts:,}")

            print("\nFinal counts:")
            cur.execute("SELECT COUNT(*) FROM actors")
            print(f"actors: {cur.fetchone()[0]:,}")

            cur.execute("SELECT COUNT(*) FROM movie_actors")
            print(f"movie_actors: {cur.fetchone()[0]:,}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()