## CASE 1:
Lost Update: "A lost update occurs when two transactions both operate on the same item, and one transaction writes a value based on an older read, overwriting a newer update made by another transaction"
# WHERE COULD IT HAPPEN 
    ```
    1. PUT /users/{user_id}/collection/{movie_id}
    Senerio:
    participant T1 as Txn A (update rating to 9.0)
    participant T2 as Txn B (update rating to 7.0)
    T1->>DB: BEGIN
    T2->>DB: BEGIN
    T1->>DB: SELECT current rating (e.g., 8.0)
    T2->>DB: SELECT current rating (e.g., 8.0)
    T1->>DB: UPDATE rating = 9.0
    T1->>DB: COMMIT
    T2->>DB: UPDATE rating = 7.0
    T2->>DB: COMMIT
    Response: Final rating=7.0; Txn A update effectively lost.
    Solution: Row-level locking. This solution is appropriate bacause it can prevent a lost update when two concurrent transactions operate on the same watched_movies row inside overlapping database transactions. 
    For this pecific case, using SELECT ... FOR UPDATE before modifying the rating forces the second transaction to wait until the first transaction commits.
    ```
![alt text](<../Screenshot 2026-05-27 at 01.18.55.png>)
    

## CASE 2:
Phantom Read: "A phantom read occurs when the same query is executed twice within a transaction, but the second execution returns a different set of rows because another transaction inserted or deleted rows that match the query condition"
# WHERE COULD IT HAPPEN 
    1. GET /users/{user_id}/recommendations
    Function of that API:
        1. Count watched movies.
        2. If < 5, return fallback list.
        3. Else compute personalized recommendations
    Senerio:
        Concurrent transactions add/remove watched movies or ratings while this decision is being made

    participant T1 as Txn A (recommendations)
    participant DB as PostgreSQL
    participant T2 as Txn B (collection updates)

    T1->>DB: BEGIN
    T1->>DB: SELECT COUNT(*) watched_movies = 4
    T2->>DB: BEGIN
    T2->>DB: INSERT/UPDATE watched_movies to 6 rated movies
    T2->>DB: COMMIT
    T1->>DB: Use fallback path because count read as 4
    T1->>DB: SELECT top_unwatched
    T1->>DB: COMMIT
    #Response is logically sinconsistent with latest committed state.
    ![alt text](<Screenshot 2026-05-27 at 10.40.05.png>)

    Solution: SERIALIZABLE and retry on serialization failure.
        - Keep retries to less than 5 times
        - Add short delay before retry under high contention
        - Return 503 when retries are exhausted
    SERIALIZABLE + retry remains a valid solution, as it safeguards the consistency of the recommendation decision with respect to the state of the `watched_movies` set.


## CASE 3:
Phantom Read: "A phantom read occurs when the same query is executed twice within a transaction, but the second execution returns a different set of rows because another transaction inserted or deleted rows that match the query condition"
# WHERE COULD IT HAPPEN 
    1. GET /users/{user_id}/insights
        This API should return top genres,top director,top actor,top decades,from multiple aggregate queries
        Therefore, concurrent writes can make each aggregate reflect a different moment in time
    participant T1 as Txn A (insights)
    participant DB as PostgreSQL
    participant T2 as Txn B (adds watched movie)

    T1->>DB: BEGIN
    T1->>DB: Query top genres (snapshot S1)
    T2->>DB: BEGIN
    T2->>DB: INSERT watched_movies + related joins
    T2->>DB: COMMIT
    T1->>DB: Query top decades (now sees new row under weak isolation)
    T1->>DB: Query top director
    T1->>DB: COMMIT
    Note over T1: Returned analytics may mix old and new states
    ![alt text](<Screenshot 2026-05-27 at 18.21.01.png>)

    Solution：REPEATABLE READ
    - guarantee one consistent snapshot for all aggregate queries
    This solution is appropriate bacause endpoint is read-analytic and should be self-consistent rather than blocking other transactions