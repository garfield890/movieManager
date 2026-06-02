# Performance Writeup

## Fake a million rows of data

Our local database uses a mix of real IMDb metadata and fake user activity.

IMDb movie import script:
[src/import_imdb_movies.py](src/import_imdb_movies.py)

IMDb genre import script:
[src/import_real_genres.py](src/import_real_genres.py)

IMDb actor import script:
[src/import_real_actors.py](src/import_real_actors.py)

IMDb director import script:
[src/import_real_directors.py](src/import_real_directors.py)

Fake user activity script:
[src/generate_fake_data.py](src/generate_fake_data.py)

Endpoint performance test script:
[src/test_endpoint_performance.py](src/test_endpoint_performance.py)

The IMDB data came from [text](https://datasets.imdbws.com/)

For this performance test, we used DBEAVER instead of the hosted database.

We used faked user data. `src/generate_fake_data.py` creates 10,000 fake users and 250,000 `watched_movies` rows. Each watched movie row randomly chooses a user and a movie. The script marks a movie as watched about 75% of the time, and if the movie is watched, it assigns a rating about 70% of the time. Ratings are generated from 1.0 to 10.0.

DATA SIZE:

```sql
SELECT 'users' AS table_name, COUNT(*) AS row_count FROM users
UNION ALL
SELECT 'movies', COUNT(*) FROM movies
UNION ALL
SELECT 'watched_movies', COUNT(*) FROM watched_movies
UNION ALL
SELECT 'logins', COUNT(*) FROM logins
UNION ALL
SELECT 'actors', COUNT(*) FROM actors
UNION ALL
SELECT 'directors', COUNT(*) FROM directors
UNION ALL
SELECT 'genres', COUNT(*) FROM genres
UNION ALL
SELECT 'movie_actors', COUNT(*) FROM movie_actors
UNION ALL
SELECT 'movie_directors', COUNT(*) FROM movie_directors
UNION ALL
SELECT 'movie_genres', COUNT(*) FROM movie_genres;
```

Result:

|table_name|row_count|
|----------|---------|
|movie_actors|4029072|
|actors|1263067|
|movie_genres|1018658|
|movies|742147|
|movie_directors|750799|
|directors|277002|
|watched_movies|250001|
|users|10001|
|logins|2|
|genres|27|

Total 8590797 rows

![alt text](<../Screenshot 2026-06-01 at 18.46.51.png>)



This exceeds the required one million rows. The distribution is realistic because it is based on real IMDb metadata.

The `users` and `watched_movies` tables model fake user behavior on top of the real IMDb metadata. In a real service, `watched_movies` would continue to grow as users save, watch, and rate movies. Our local data currently has 10,000 users and 250,000 watched movie records, which gives each user a realistic collection size while still keeping the database small enough to test locally.

## Performance Results of Hitting Endpoints

Endpoint performance was measured with the script:
[src/test_endpoint_performance.py](src/test_endpoint_performance.py)

Result:

| Endpoint | Status | Min ms | Avg ms | Max ms | Notes |
|---|---:|---:|---:|---:|---|
| GET / | 200 | 3.28 | 3.58 | 3.74 | Root endpoint |
| GET /health/ | 200 | 2.74 | 3.34 | 3.88 | Health check |
| POST /users/login | 401 | 6.19 | 6.94 | 7.52 | Invalid username path |
| GET /movies/external/search/{title}/{year} | 200 | 6.81 | 7.46 | 7.90 | Movie title/year lookup |
| GET /movies/trending/{days} | 200 | 4113.37 | 4276.32 | 4580.32 | Slowest endpoint |
| POST /users/{token}/collection/add_by_title | 200 | 4.98 | 6.47 | 8.91 | Add by title |
| POST /users/{token}/collection/{movie_id} | 200 | 5.38 | 5.48 | 5.62 | Add by movie id |
| PUT /users/{token}/collection/{movie_id} | 200 | 4.80 | 5.11 | 5.57 | Update collection entry |
| GET /users/{token}/collection | 200 | 5.08 | 5.40 | 6.03 | User collection |
| GET /users/{token}/collection/filter | 200 | 16.68 | 18.62 | 20.75 | Filter collection by genre |
| GET /users/{token}/recommendations | 200 | 2090.71 | 2250.51 | 2517.60 | Second slowest endpoint |
| GET /users/{token}/insights | 200 | 8.84 | 9.91 | 11.92 | User insight aggregation |
| GET /users/leaderboard/{genre}/{limit} | 200 | 173.91 | 180.49 | 189.01 | Leaderboard aggregation |
| DELETE /users/{token}/collection/{movie_id} | 500 | 5.19 | 10.99 | 21.73 | Internal Server Error |
The slowest endpoint was:

```text
GET /movies/trending/{days}
Average time: 4276.32 ms
```

## Performance Tuning

### Slow Endpoint Query

The original query was:

```sql
SELECT movies.movie_id,
       movies.movie_name,
       movies.year AS release_year,
       movies.imdb_rating,
       movies.runtime,
       movies.mpaa_rating,
       movies.plot,
       COUNT(*) as watch_count
FROM movies
JOIN watched_movies wm ON wm.movie_id = movies.movie_id
WHERE wm.date_added >= CURRENT_DATE - 30
GROUP BY movies.movie_id,
         movies.movie_name,
         movies.year,
         movies.imdb_rating,
         movies.runtime,
         movies.mpaa_rating,
         movies.plot
ORDER BY watch_count DESC;
```

This query finds movies that were added to `watched_movies` in the last 30 days, counts how many times each movie appears, and orders movies by that count.

### EXPLAIN

```sql
EXPLAIN
SELECT movies.movie_id,
       movies.movie_name,
       movies.year AS release_year,
       movies.imdb_rating,
       movies.runtime,
       movies.mpaa_rating,
       movies.plot,
       COUNT(*) as watch_count
FROM movies
JOIN watched_movies wm ON wm.movie_id = movies.movie_id
WHERE wm.date_added >= CURRENT_DATE - 30
GROUP BY movies.movie_id,
         movies.movie_name,
         movies.year,
         movies.imdb_rating,
         movies.runtime,
         movies.mpaa_rating,
         movies.plot
ORDER BY watch_count DESC;
```

```text
Sort  (cost=91448.95..92073.95 rows=250000 width=53)
  Sort Key: (count(*)) DESC
  ->  Finalize GroupAggregate  (cost=31075.98..60487.49 rows=250000 width=53)
        Group Key: movies.movie_id
        ->  Gather Merge  (cost=31075.98..56945.82 rows=208334 width=53)
              Workers Planned: 2
              ->  Partial GroupAggregate  (cost=30075.96..31898.88 rows=104167 width=53)
                    Group Key: movies.movie_id
                    ->  Sort  (cost=30075.96..30336.38 rows=104167 width=45)
                          Sort Key: movies.movie_id
                          ->  Parallel Hash Join  (cost=6250.77..18188.40 rows=104167 width=45)
                                Hash Cond: (movies.movie_id = wm.movie_id)
                                ->  Parallel Seq Scan on movies  (cost=0.00..10165.28 rows=309228 width=45)
                                ->  Parallel Hash  (cost=4412.53..4412.53 rows=147059 width=4)
                                      ->  Parallel Seq Scan on watched_movies wm  (cost=0.00..4412.53 rows=147059 width=4)
                                            Filter: (date_added >= (CURRENT_DATE - 30))
```

### Original EXPLAIN ANALYZE

```text
Sort  (cost=91448.95..92073.95 rows=250000 width=53) (actual time=404.976..432.545 rows=212570 loops=1)
  Sort Key: (count(*)) DESC
  Sort Method: external merge  Disk: 14072kB
  ->  Finalize GroupAggregate  (cost=31075.98..60487.49 rows=250000 width=53) (actual time=194.501..343.119 rows=212570 loops=1)
        Group Key: movies.movie_id
        ->  Gather Merge  (cost=31075.98..56945.82 rows=208334 width=53) (actual time=194.495..273.178 rows=212570 loops=1)
              Workers Planned: 2
              Workers Launched: 2
              ->  Partial GroupAggregate  (cost=30075.96..31898.88 rows=104167 width=53) (actual time=190.018..228.023 rows=70857 loops=3)
                    Group Key: movies.movie_id
                    ->  Sort  (cost=30075.96..30336.38 rows=104167 width=45) (actual time=190.010..197.253 rows=83334 loops=3)
                          Sort Key: movies.movie_id
                          Sort Method: external merge  Disk: 4528kB
                          Worker 0:  Sort Method: external merge  Disk: 4440kB
                          Worker 1:  Sort Method: external merge  Disk: 4424kB
                          ->  Parallel Hash Join  (cost=6250.77..18188.40 rows=104167 width=45) (actual time=34.107..157.168 rows=83334 loops=3)
                                Hash Cond: (movies.movie_id = wm.movie_id)
                                ->  Parallel Seq Scan on movies  (cost=0.00..10165.28 rows=309228 width=45) (actual time=0.011..43.059 rows=247382 loops=3)
                                ->  Parallel Hash  (cost=4412.53..4412.53 rows=147059 width=4) (actual time=33.429..33.430 rows=83334 loops=3)
                                      Buckets: 262144  Batches: 1  Memory Usage: 11872kB
                                      ->  Parallel Seq Scan on watched_movies wm  (cost=0.00..4412.53 rows=147059 width=4) (actual time=0.012..15.233 rows=83334 loops=3)
                                            Filter: (date_added >= (CURRENT_DATE - 30))
Planning Time: 0.251 ms
Execution Time: 439.815 ms
```

The original SQL query execution time was: 439.815 ms

From the analyze we can see it is slow because it first scans watched_movies, which has 250,000 rows. Second, It joins those rows to the movies table, which has 742,147 rows. Third, It sorts 212,570 grouped movie results

The API endpoint was much slower than the SQL execution time because the original query produced 212,570 rows. Returning and serializing that many movie records as JSON adds significant endpoint overhead.

### First Try

We first tried to add an index on `(date_added, movie_id)`:

```sql
CREATE INDEX idx_watched_movies_date_added_movie_id
ON watched_movies (date_added, movie_id);
```

We expected this to help because the query filters by date_added and joins by movie_id.

EXPLAIN ANALYZE after adding this index:

```text
Sort  (cost=91449.07..92074.07 rows=250001 width=53) (actual time=394.317..422.160 rows=212570 loops=1)
  Sort Key: (count(*)) DESC
  Sort Method: external merge  Disk: 14072kB
  ->  Finalize GroupAggregate  (cost=31075.99..60487.51 rows=250001 width=53) (actual time=183.346..334.071 rows=212570 loops=1)
        Group Key: movies.movie_id
        ->  Gather Merge  (cost=31075.99..56945.83 rows=208334 width=53) (actual time=183.338..263.550 rows=212570 loops=1)
              Workers Planned: 2
              Workers Launched: 2
              ->  Partial GroupAggregate  (cost=30075.97..31898.89 rows=104167 width=53) (actual time=178.614..217.042 rows=70857 loops=3)
                    Group Key: movies.movie_id
                    ->  Sort  (cost=30075.97..30336.39 rows=104167 width=45) (actual time=178.607..186.072 rows=83334 loops=3)
                          Sort Key: movies.movie_id
                          Sort Method: external merge  Disk: 4528kB
                          Worker 0:  Sort Method: external merge  Disk: 4416kB
                          Worker 1:  Sort Method: external merge  Disk: 4448kB
                          ->  Parallel Hash Join  (cost=6250.78..18188.41 rows=104167 width=45) (actual time=33.816..147.252 rows=83334 loops=3)
                                Hash Cond: (movies.movie_id = wm.movie_id)
                                ->  Parallel Seq Scan on movies  (cost=0.00..10165.28 rows=309228 width=45) (actual time=0.012..40.939 rows=247382 loops=3)
                                ->  Parallel Hash  (cost=4412.54..4412.54 rows=147059 width=4) (actual time=33.192..33.193 rows=83334 loops=3)
                                      Buckets: 262144  Batches: 1  Memory Usage: 11872kB
                                      ->  Parallel Seq Scan on watched_movies wm  (cost=0.00..4412.54 rows=147059 width=4) (actual time=0.012..15.569 rows=83334 loops=3)
                                            Filter: (date_added >= (CURRENT_DATE - 30))
Planning Time: 0.231 ms
Execution Time: 429.169 ms
```

Result:
Before: 439.815 ms
After idx_watched_movies_date_added_movie_id: 429.169 ms

The improvement is not significant

The index did not help because `date_added >= CURRENT_DATE - 30` matched almost every row in `watched_movies` (Because our fake data). Since the filter was not selective, PostgreSQL still chose a sequential scan instead of the new index. Also, the query groups by `movie_id`, but this index is ordered primarily by `date_added`, so it does not help the grouping step much.

### Second Index Attempt

Next, we tried an index on `movie_id`:

```sql
CREATE INDEX idx_watched_movies_movie_id
ON watched_movies (movie_id);
```

We expected this to help the join and grouping by `movie_id`.

EXPLAIN ANALYZE:

```text
Sort  (cost=81685.13..82310.14 rows=250001 width=53) (actual time=563.104..588.957 rows=212570 loops=1)
  Sort Key: (count(*)) DESC
  Sort Method: external merge  Disk: 14072kB
  ->  GroupAggregate  (cost=4.27..50723.58 rows=250001 width=53) (actual time=0.037..493.984 rows=212570 loops=1)
        Group Key: movies.movie_id
        ->  Merge Join  (cost=4.27..46973.56 rows=250001 width=45) (actual time=0.027..394.588 rows=250001 loops=1)
              Merge Cond: (movies.movie_id = wm.movie_id)
              ->  Index Scan using movies_pkey on movies  (cost=0.42..26356.66 rows=742147 width=45) (actual time=0.012..151.851 rows=742147 loops=1)
              ->  Index Scan using idx_watched_movies_movie_id on watched_movies wm  (cost=0.42..15637.36 rows=250001 width=4) (actual time=0.012..172.843 rows=250001 loops=1)
                    Filter: (date_added >= (CURRENT_DATE - 30))
Planning Time: 1.181 ms
Execution Time: 595.224 ms
```

Result:
Before: 439.815 ms
After: 595.224 ms

This made the query slower.

The reason is that PostgreSQL changed from a parallel hash join to a merge join using index scans. Even though it used indexes, it still scanned nearly all 250,000 rows in `watched_movies` and all 742,147 rows in `movies`. The final external merge sort over 212,570 grouped rows also remained.

### Revise

The original query joined `watched_movies` to the large `movies` table before aggregation, then sorted and returned every grouped movie result.

For a trending endpoint, returning every trending movie is unnecessary. The API should return the top trending movies. We decided to make the query only return top 100 movies.

Rewritten query:

```sql
EXPLAIN ANALYZE
WITH trending_counts AS (
    SELECT wm.movie_id, COUNT(*) AS watch_count
    FROM watched_movies wm
    WHERE wm.date_added >= CURRENT_DATE - 30
    GROUP BY wm.movie_id
    ORDER BY watch_count DESC
    LIMIT 100
)
SELECT m.movie_id,
       m.movie_name,
       m.year AS release_year,
       m.imdb_rating,
       m.runtime,
       m.mpaa_rating,
       m.plot,
       tc.watch_count
FROM trending_counts tc
JOIN movies m ON m.movie_id = tc.movie_id
ORDER BY tc.watch_count DESC;
```

EXPLAIN ANALYZE after rewriting the query while using `idx_watched_movies_movie_id`:

```text
Nested Loop  (cost=23789.96..23958.63 rows=100 width=53) (actual time=217.798..217.930 rows=100 loops=1)
  ->  Limit  (cost=23789.53..23789.58 rows=100 width=12) (actual time=217.758..217.761 rows=100 loops=1)
        ->  Sort  (cost=23789.53..24260.87 rows=188534 width=12) (actual time=217.757..217.759 rows=100 loops=1)
              Sort Key: (count(*)) DESC
              Sort Method: top-N heapsort  Memory: 25kB
              ->  GroupAggregate  (cost=0.42..18772.71 rows=188534 width=12) (actual time=0.038..194.921 rows=212570 loops=1)
                    Group Key: wm.movie_id
                    ->  Index Scan using idx_watched_movies_movie_id on watched_movies wm  (cost=0.42..15637.36 rows=250001 width=4) (actual time=0.028..145.047 rows=250001 loops=1)
                          Filter: (date_added >= (CURRENT_DATE - 30))
  ->  Index Scan using movies_pkey on movies m  (cost=0.42..8.44 rows=1 width=45) (actual time=0.008..0.008 rows=1 loops=100)
        Index Cond: (movie_id = wm.movie_id)
Planning Time: 0.772 ms
Execution Time: 217.991 ms
```

Result:
Original: 439.815 ms
Limit 100: 217.991 ms

This was faster, but not fast enough. The LIMIT 100 fixed the final result size, changed the sort to an top-N heapsort ( Sort Method: top-N heapsort Memory: 29kB), and reduced the final join to 100 movie rows. However, PostgreSQL still had to scan 250,001 rows.

### Final Fix

The rewritten query only needs movie_id and date_added.
We added a composite index ordered by `movie_id` first:

```sql
CREATE INDEX idx_watched_movies_movie_id_date_added
ON watched_movies (movie_id, date_added);
```

This index is better than `(date_added, movie_id)` for the rewritten query because the expensive aggregation groups by `movie_id`.

```
Nested Loop  (cost=17422.51..18259.59 rows=100 width=53) (actual time=129.508..129.984 rows=100 loops=1)
  Buffers: shared hit=1062
  ->  Limit  (cost=17422.09..17422.34 rows=100 width=12) (actual time=129.484..129.500 rows=100 loops=1)
        Buffers: shared hit=662
        ->  Sort  (cost=17422.09..17896.00 rows=189564 width=12) (actual time=129.482..129.491 rows=100 loops=1)
              Sort Key: (count(*)) DESC
              Sort Method: top-N heapsort  Memory: 29kB
              Buffers: shared hit=662
              ->  GroupAggregate  (cost=0.42..10177.09 rows=189564 width=12) (actual time=0.062..101.194 rows=212570 loops=1)
                    Group Key: wm.movie_id
                    Buffers: shared hit=662
                    ->  Index Only Scan using idx_watched_movies_movie_id_date_added on watched_movies wm  (cost=0.42..7031.44 rows=250001 width=4) (actual time=0.057..33.347 rows=250001 loops=1)
                          Index Cond: (date_added >= (CURRENT_DATE - 30))
                          Heap Fetches: 0
                          Buffers: shared hit=662
  ->  Index Scan using movies_pkey on movies m  (cost=0.42..8.36 rows=1 width=45) (actual time=0.004..0.004 rows=1 loops=100)
        Index Cond: (movie_id = wm.movie_id)
        Buffers: shared hit=400
Planning Time: 0.210 ms
Execution Time: 130.029 ms
```

Result:
Original query: 439.815 ms
Final optimized query: 130.029 ms

Improvement:
The execution time decreased by about:

```text
(439.815 - 130.029) / 439.815 = about 70.4%
```

This is acceptable for our service. The trending endpoint is an analytics-style endpoint that computes popularity from user activity. A final SQL execution time about 100 ms on production-like local data is fast enough for an interactive API.

The most important improvement in the final plan is:

```text
Index Only Scan using idx_watched_movies_movie_id_date_added
Heap Fetches: 0
```

This means PostgreSQL reads the needed `watched_movies` values directly from the index without fetching rows from the table heap.

### Retest on API 

Result:

| Endpoint | Status | Min ms | Avg ms | Max ms | Error |
|---|---:|---:|---:|---:|---|
| GET / | 200 | 3.20 | 3.28 | 3.36 |  |
| GET /health/ | 200 | 4.74 | 9.01 | 16.81 |  |
| POST /users/login | 401 | 8.57 | 11.40 | 15.21 | {"detail":"Invalid username"} |
| GET /movies/external/search/{title}/{year} | 200 | 8.01 | 9.42 | 11.70 |  |
| GET /movies/trending/{days} | 200 | 132.96 | 204.79 | 249.43 |  |
| POST /users/{token}/collection/add_by_title | 200 | 10.61 | 11.82 | 14.19 |  |
| POST /users/{token}/collection/{movie_id} | 200 | 8.89 | 9.64 | 10.57 |  |
| PUT /users/{token}/collection/{movie_id} | 200 | 10.08 | 19.50 | 37.78 |  |
| GET /users/{token}/collection | 200 | 8.96 | 10.84 | 13.12 |  |
| GET /users/{token}/collection/filter | 200 | 26.68 | 27.54 | 28.35 |  |
| GET /users/{token}/recommendations | 200 | 3297.74 | 3405.83 | 3525.86 |  |
| GET /users/{token}/insights | 200 | 12.14 | 13.29 | 15.23 |  |
| GET /users/leaderboard/{genre}/{limit} | 200 | 242.38 | 256.24 | 272.81 |  |
| DELETE /users/{token}/collection/{movie_id} | 404 | 7.18 | 7.49 | 8.06 | {"detail":"Collection entry not found"} |

Endpoint tuned: GET /movies/trending/{days}

Initial: AVG 4276.32 ms

After tuning: AVG 204.79 ms

Improvement:

```text
(4276.32 - 204.79) / 4276.32 = 95.2%
```

## Conclusion 
After tuning, the slowest endpoint's run time was reduced 95.2% from 4276.32 ms to 204.79 ms and 70.4% at the SQL level from 439.815 ms to 130.029 ms at the SQL level.
We could proudly conclude that this tuning is successful.
