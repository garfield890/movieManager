## CASE 1:
Lost Update: "A lost update occurs when two transactions both operate on the same item, and one transaction writes a value based on an older read, overwriting a newer update made by another transaction"
# WHERE COULD IT HAPPEN 
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
    Note over DB: Final rating=7.0; Txn A update effectively lost.
    ![alt text](<Screenshot 2026-05-27 at 01.18.55.png>)

    Solution: Row-level locking. It can prevent a lost update when two concurrent transactions operate on the same watched_movies row inside overlapping database transactions. 
    For this pecific case, using SELECT ... FOR UPDATE before modifying the rating forces the second transaction to wait until the first transaction commits.
    