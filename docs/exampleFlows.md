# Example Flows — Movie Manager

Three example user flows showing how the endpoints in `API_spec.md` come together.

## Flow 1 — Signing Up and Saving a New Favorite

Priya just watched Inception for the first time and loved it. She decides to start keeping a list of films she has seen, so she signs up for Movie Manager and saves Inception as her first entry.

She calls POST /users/register with her username, email, and password. The server hands back her new user_id of 1042.

{ "user_id": 1042, "username": "priya_watches" }

She logs in via POST /users/login to get a session token, then searches the external catalog with GET /movies/external/search/inception/2010. One match comes back with external_id tt1375666.

Finally, she adds it to her collection by calling POST /users/1042/collection/tt1375666 with body { "watched": true }.

{ "user_id": 1042, "external_id": "tt1375666", "watched": true, "rating": null }

Right after that, she rates it by calling PUT /users/1042/collection/tt1375666 with body { "rating": 9.5, "watched": true }.

{ "rating": 9.5, "watched": true }

Priya is set up with her first saved and rated movie.

## Flow 2 — Picking a Top Sci-Fi Film to Recommend

Marcus wants to recommend a new film to his partner tonight, but first he needs to finish rating Arrival, which he watched last week.

He logs in with POST /users/login (user_id 2058) and then rates Arrival by calling PUT /users/2058/collection/tt2543164 with body { "rating": 8.5, "watched": true }.

{ "rating": 8.5, "watched": true }

With that out of the way, he pulls up his top sci-fi picks by calling GET /users/2058/collection/filter/genre/sci-fi.

{
  "collection": [
    { "external_id": "tt1375666", "title": "Inception", "rating": 9.5, "release_year": 2010 },
    { "external_id": "tt2543164", "title": "Arrival",   "rating": 8.5, "release_year": 2016 }
  ]
}

To go beyond simple CRUD, he also asks the API for personalized suggestions with GET /users/2058/recommendations. The response puts Interstellar near the top with a strong predicted rating, so that becomes his recommendation for the night.

{
  "recommendations": [
    { "external_id": "tt0816692", "title": "Interstellar", "predicted_rating": 9.2 }
  ]
}

## Flow 3 — Tidying Up a Director Shelf

Lina has been on a Denis Villeneuve kick and wants to clean up her library: add Blade Runner 2049, drop Dune: Part One, and see the end result.

She logs in via POST /users/login (user_id 3311) and searches for Blade Runner 2049 with GET /movies/external/search/blade_runner_2049/2017. She finds it with external_id tt1856101.

She adds it to her collection via POST /users/3311/collection/tt1856101 with body { "watched": true }, then rates it with PUT /users/3311/collection/tt1856101 and body { "rating": 9.0, "watched": true }.

{ "rating": 9.0, "watched": true }

Dune: Part One no longer feels like a favorite, so she drops it with POST /users/3311/collection/tt1160419/remove.

{ "user_id": 3311, "external_id": "tt1160419", "removed": true }

Finally she checks the updated shelf with GET /users/3311/collection/filter/director/denis_villnueve

{
  "collection": [
    { "external_id": "tt2543164", "title": "Arrival",           "release_year": 2016, "rating": 8.5 },
    { "external_id": "tt1856101", "title": "Blade Runner 2049", "release_year": 2017, "rating": 9.0 }
  ]
}

She finishes by calling GET /users/3311/insights to see what her watched list says about her current tastes.

{
  "favorite_genres": ["Science Fiction", "Drama"],
  "top_director": "Denis Villeneuve",
  "most_watched_decade": "2010s"
}

Her Villeneuve shelf now matches her current taste, and the API can summarize that taste as well.
