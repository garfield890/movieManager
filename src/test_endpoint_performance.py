import os
import json
import statistics
import time
from collections.abc import Callable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import psycopg
from dotenv import load_dotenv


BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
RUNS = int(os.getenv("PERF_RUNS", "3"))
TIMEOUT_SECONDS = float(os.getenv("PERF_TIMEOUT_SECONDS", "60"))
PERF_TOKEN_PREFIX = "perf-test-token"

class SimpleResponse:
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text

    def json(self) -> dict:
        return json.loads(self.text)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}: {self.text[:200]}")


def request(
    method: str,
    path: str,
    headers: dict,
    json_body: dict | None = None,
    params: dict | None = None,
) -> SimpleResponse:
    url = f"{BASE_URL}{path}"
    if params:
        url = f"{url}?{urlencode(params)}"

    body = None
    request_headers = dict(headers)
    if json_body is not None:
        body = json.dumps(json_body).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    req = Request(url, data=body, headers=request_headers, method=method)
    try:
        with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            text = response.read().decode("utf-8")
            return SimpleResponse(response.status, text)
    except HTTPError as exc:
        text = exc.read().decode("utf-8")
        return SimpleResponse(exc.code, text)


def timed_request(label: str, request_fn: Callable[[], SimpleResponse]) -> dict:
    timings = []
    statuses = []
    errors = []

    for _ in range(RUNS):
        start = time.perf_counter()
        try:
            response = request_fn()
            elapsed_ms = (time.perf_counter() - start) * 1000
            timings.append(elapsed_ms)
            statuses.append(response.status_code)
            if response.status_code >= 400:
                errors.append(response.text[:200])
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            timings.append(elapsed_ms)
            statuses.append("ERROR")
            errors.append(str(exc))

    return {
        "endpoint": label,
        "status": statuses[-1],
        "min_ms": min(timings),
        "avg_ms": statistics.mean(timings),
        "max_ms": max(timings),
        "error": errors[-1] if errors else "",
    }


def get_heavy_user_token(conn: psycopg.Connection) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT user_id
            FROM watched_movies
            GROUP BY user_id
            ORDER BY COUNT(*) DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("No watched_movies rows found for performance testing.")

        user_id = row[0]
        token = f"{PERF_TOKEN_PREFIX}-{user_id}"

        cur.execute(
            """
            INSERT INTO logins (user_id, login_token)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET login_token = EXCLUDED.login_token
            """,
            (user_id, token),
        )
        conn.commit()

    return token


def get_sample_movie(conn: psycopg.Connection) -> tuple[int, str, int]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT movie_id, movie_name, year
            FROM movies
            WHERE year IS NOT NULL
            ORDER BY movie_id
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("No movies found for performance testing.")
        return row


def create_temp_user_token(headers: dict) -> str:
    suffix = int(time.time() * 1000) % 1_000_000_000
    username = f"perf{suffix}"
    password = "PerfPass123"

    register = request(
        "POST",
        "/users/register",
        headers,
        json_body={
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
        },
    )
    register.raise_for_status()

    login = request(
        "POST",
        "/users/login",
        headers,
        json_body={
            "username": username,
            "password": password,
        },
    )
    login.raise_for_status()
    return login.json()["token"]


def print_markdown_table(results: list[dict]) -> None:
    print("| Endpoint | Status | Min ms | Avg ms | Max ms | Error |")
    print("|---|---:|---:|---:|---:|---|")
    for result in results:
        print(
            "| {endpoint} | {status} | {min_ms:.2f} | {avg_ms:.2f} | "
            "{max_ms:.2f} | {error} |".format(**result)
        )


def main() -> None:
    load_dotenv()

    api_key = os.environ["API_KEY"]
    postgres_uri = os.environ["POSTGRES_URI"]
    headers = {"access_token": api_key}

    with psycopg.connect(postgres_uri) as conn:
        heavy_token = get_heavy_user_token(conn)
        movie_id, movie_title, movie_year = get_sample_movie(conn)

    temp_token = create_temp_user_token(headers)

    tests = [
        (
            "GET /",
            lambda: request("GET", "/", headers),
        ),
        (
            "GET /health/",
            lambda: request("GET", "/health/", headers),
        ),
        (
            "POST /users/login",
            lambda: request(
                "POST",
                "/users/login",
                headers,
                json_body={"username": "not_a_real_user", "password": "wrongpass123"},
            ),
        ),
        (
            "GET /movies/external/search/{title}/{year}",
            lambda: request(
                "GET",
                f"/movies/external/search/{movie_title.replace(' ', '_')}/{movie_year}",
                headers,
            ),
        ),
        (
            "GET /movies/trending/{days}",
            lambda: request("GET", "/movies/trending/30", headers),
        ),
        (
            "POST /users/{token}/collection/add_by_title",
            lambda: request(
                "POST",
                f"/users/{temp_token}/collection/add_by_title",
                headers,
                json_body={"title": movie_title, "year": movie_year, "watched": True},
            ),
        ),
        (
            "POST /users/{token}/collection/{movie_id}",
            lambda: request(
                "POST",
                f"/users/{temp_token}/collection/{movie_id}",
                headers,
                json_body={"watched": True},
            ),
        ),
        (
            "PUT /users/{token}/collection/{movie_id}",
            lambda: request(
                "PUT",
                f"/users/{temp_token}/collection/{movie_id}",
                headers,
                json_body={"watched": True, "rating": 8.5},
            ),
        ),
        (
            "GET /users/{token}/collection",
            lambda: request("GET", f"/users/{heavy_token}/collection", headers),
        ),
        (
            "GET /users/{token}/collection/filter",
            lambda: request(
                "GET",
                f"/users/{heavy_token}/collection/filter",
                headers,
                params={"genre": "Drama"},
            ),
        ),
        (
            "GET /users/{token}/recommendations",
            lambda: request("GET", f"/users/{heavy_token}/recommendations", headers),
        ),
        (
            "GET /users/{token}/insights",
            lambda: request("GET", f"/users/{heavy_token}/insights", headers),
        ),
        (
            "GET /users/leaderboard/{genre}/{limit}",
            lambda: request(
                "GET",
                "/users/leaderboard/Drama/10",
                headers,
                params={"sort_by": "movies_watched"},
            ),
        ),
        (
            "DELETE /users/{token}/collection/{movie_id}",
            lambda: request(
                "DELETE",
                f"/users/{temp_token}/collection/{movie_id}",
                headers,
            ),
        ),
    ]
    results = [timed_request(label, request_fn) for label, request_fn in tests]
    print_markdown_table(results)
    slowest = max(results, key=lambda result: result["avg_ms"])
    print()
    print(
        "Slowest endpoint: {endpoint} ({avg_ms:.2f} ms average)".format(
            **slowest
        )
    )


if __name__ == "__main__":
    main()
