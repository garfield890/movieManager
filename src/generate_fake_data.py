import os
import random
from decimal import Decimal

import psycopg
from dotenv import load_dotenv


NUM_USERS = 10_000
NUM_WATCHED_MOVIES = 250_000
BATCH_SIZE = 5_000


def main():
    load_dotenv()
    conn = psycopg.connect(os.environ["POSTGRES_URI"])

    with conn.cursor() as cur:
        #generate users
        users = [
            (f"user_{i}", f"user_{i}@example.com", "fake_password")
            for i in range(1, NUM_USERS + 1)
        ]

        cur.executemany(
            """
            INSERT INTO users (username, email, password)
            VALUES (%s, %s, %s)
            ON CONFLICT (username) DO NOTHING
            """,
            users,
        )
        conn.commit()

        cur.execute("SELECT user_id FROM users")
        user_ids = [row[0] for row in cur.fetchall()]

        cur.execute("SELECT movie_id FROM movies")
        movie_ids = [row[0] for row in cur.fetchall()]

        watched_rows = set()

        while len(watched_rows) < NUM_WATCHED_MOVIES:
            user_id = random.choice(user_ids)
            movie_id = random.choice(movie_ids)
            watched = random.random() < 0.75
            if watched and random.random() < 0.7:
                rating = Decimal(str(round(random.uniform(1.0, 10.0), 1)))
            else:
                rating = None

            watched_rows.add((user_id, movie_id, watched, rating))

            if len(watched_rows) % BATCH_SIZE == 0:
                print(f"Generated {len(watched_rows):,} watched rows...")

        watched_rows = list(watched_rows)

        for i in range(0, len(watched_rows), BATCH_SIZE):
            batch = watched_rows[i:i + BATCH_SIZE]
            cur.executemany(
                """
                INSERT INTO watched_movies (user_id, movie_id, watched, rating)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, movie_id) DO NOTHING
                """,
                batch,
            )
            conn.commit()
            print(f"Inserted {i + len(batch):,} watched rows...")

    conn.close()


if __name__ == "__main__":
    main()