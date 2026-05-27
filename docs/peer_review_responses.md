# Peer Review Responses

## Pihu — Code Review (CR)

1. **Fixed** — Implemented password hashing with argon2
2. **Fixed** — Added more robust login endpoint; all endpoints now rely on login token rather than just user id
3. **Fixed** — Removed print statement
4. **Fixed** — Added email validation
5. **Fixed** — Added min password length
6. **Fixed** — All endpoints check if user exists now
7. **Fixed** — Exceptions are thrown if removal is unsuccessful
8. **Fixed** — See Pihu CR#6
9. **Already Fixed** — Other fields for this endpoint are optional. Rating is the only one required, so it is already possible to only update the rating.
10. **Fixed** — Condensed all filters into one filter endpoint with optional inputs
11. **Fixed** — Rounded predicted rating
12. **Fixed** — Can't really *automatically* add it to the list since we wouldn't know what genre to map it to. Did add functionality to add failed genre to table, so that dev team can manually add to Genre Aliases for future use.

## Pihu — Schema / API (SAPI)

1. **Fixed** — See Pihu CR#1
2. **Fixed** — See Pihu CR#4
3. **Fixed** — Changed column name
4. **Fixed** — Added created_at timestamp for users and updated_at timestamp for watched_movies
5. **Fixed** — Added date_added field in watched_movies
6. **Fixed** — See Pihu CR#10
7. **Fixed** — Added new endpoint to add by title and year
8. **Fixed** — Added fallback so that it will show movies with the same title if title and year do not exist
9. **Skipped** — Would be an interesting change, but would require us to manually add franchise ids or sequel ids to each movie which is difficult for 250 movies.
10. **Skipped** — See Pihu SAPI#9
11. **Fixed** — See Pihu SAPI#2. This still requires user to input login_token but otherwise it's not really possible to do it without storing the login token in the browser cookies/cache or something.
12. **Fixed** — Added short reason for why movie was recommended.

## Pihu — Product Ideas (PI)

1. **Skipped** — Similar to recommendations, just repeated
2. **Skipped** — Similar to insights, just for two users.

---

## Nicolas — Code Review (CR)

1. **Fixed** — Added error message if incorrect movie or year is provided.
2. **Fixed** — See Pihu CR#1
3. **Fixed** — Added option to choose limits for insights with default being 3.
4. **Skipped** — Top unwatched is only for if they have not watched enough movies in general. 5 as the standard number of recommendations provided should be good, and there should be no need to make it an input.
5. **Fixed** — See Pihu CR#4
6. **Fixed** — See Pihu CR#5, added max and min length for username
7. **Fixed** — See Pihu CR#6
8. **Skipped** — Agree with the comment, but pagination would not work well in the docs page just because of how things are displayed.
9. **Fixed** — Null rated movies are now sorted to be at the end.
10. **Fixed** — Made rating optional and added check to make sure watched is True before updating rating
11. **Fixed** — Added extra check to only get movies with watched = True. Ideally, users only add movies that are watched = True (mainly for debugging purposes).
12. **Fixed** — See Pihu CR#2. Login token should fix this as it is only given to that user, requires password, and is partially random.

## Nicolas — Schema / API (SAPI)

1. **Fixed** — See Pihu CR#4
2. **Fixed** — See Pihu CR#1
3. **Fixed** — Added runtime column to movies
4. **Fixed** — See Nicolas CR#6
5. **Fixed** — Added mpaa rating column to movies. Storing birthdays may be a security risk (at least storing them in the way we know how).
6. **Fixed** — See Pihu SAPI#4 and #5
7. **Skipped** — Watch status ideally should always be true; feature could be useful but is not going to be used much
8. **Fixed** — Added plot column to movies
9. **Fixed** — Top unwatched now returns 5 movies from different genres
10. **Fixed** — See Pihu SAPI#12
11. **Skipped** — Movie year should be nullable in case the data in the dataset is empty
12. **Fixed** — See Pihu CR#5, added max password length

## Nicolas — Product Ideas (PI)

1. **Fixed** — Added trending endpoint in movies.py (Not complex endpoint)
2. **Fixed** — Added leaderboard endpoint in users.py (Complex endpoint)

---

## Angel — Code Review (CR)

1. **Fixed** — See Pihu CR#1
2. **Skipped** — Duplicate accounts are already prevented and inputs are validated
3. **Fixed** — See Pihu CR#5 and Nicolas SAPI#12
4. **Fixed** — See Nicolas CR#1
5. **Fixed** — See Pihu CR#2
6. **Fixed** — See Pihu CR#6
7. **Skipped** — This endpoint updates movies and returns the movie. Get collection should not limit because you want to see all the movies you have added.
8. **Fixed** — See Pihu CR#6
9. **Fixed** — Changed from POST to DELETE
10. **Skipped** — This endpoint returns only one movie (or max 3 if not there)
11. **Fixed** — Renamed to title for consistency
12. **Skipped** — Overkill for this assignment

## Angel — Product Ideas (PI)

1. **Fixed** — Added trending endpoint, see Nicolas PI#1
2. **Skipped** — Difficult to manage a comment section in a small-scale assignment like this.

## Angel —  Schema / API (SAPI)

1. **Fixed** — See Pihu CR#1
2. **Skipped** — True, but they need to input username as well which for this project should be okay
3. **Fixed** — See Nicolas CR#1
4. **Skipped** — See Angel SAPI #2
5. **Fixed** — See Pihu CR#6
6. **Skipped** — See Angel CR#12
7. **Fixed** — See Pihu CR#5, special character requirements would make it difficult to test
8. **Skipped** — Sure, but there are already plenty of sites that generate strong passwords.
9. **Skipped** — Only 250 movies can be added, and we do want to see all the movies. Pagination would help, but would be difficult with the /docs page.
10. **Fixed** — See Angel CR#11
11. **Fixed** — See Angel CR#9
12. **Fixed** — See Pihu CR#2