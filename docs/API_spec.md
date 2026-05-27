# API Specification — Movie Tracker

## 1. Register a New User

POST /users/register

Creates a new user account. Takes a username, email, and password and returns the new user_id.

Example response:

{ "user_id": 1042, "username": "cinemafan42" }

## 2. Log In

POST /users/login

Authenticates an existing user using their username and password, and returns a session token.

Example response:

{ "user_id": 1042, "token": "eyJhbGciOiJIUzI1NiIs..." }

## 3. Search the External Movie Database

GET /movies/external/search/{title}/{year}

Searches an external movie database for films matching a query. Accepts a title and year. Returns a list of matches with their external_id, title, release year, director, lead actor, genre, etc.

Example response:

{
  "results": [
    {
      "external_id": "tt1375666",
      "title": "Inception",
      "release_year": 2010,
      "director": "Christopher Nolan",
      "lead_actor": "Leonardo DiCaprio",
      "genre": "Science Fiction"
    }
  ]
}

## 4. Get a User's Saved Movies

GET /users/{user_id}/movies

Returns movies saved in users' collections, using metadata associated with each movie's external source record.

Example response:

{
  "movies": [
    {
      "external_id": "tt1375666",
      "title": "Inception",
      "release_year": 2010,
      "director": "Christopher Nolan",
      "lead_actor": "Leonardo DiCaprio",
      "genre": "Science Fiction"
    }
  ]
}

## 5. Get a Single Movie's Details

GET /users/{user_id}/collection/{external_id}

Returns the full details for a single saved movie, including its external movie database information and any user-specific tracking data.

Example response:

{
  "external_id": "tt1375666",
  "title": "Inception",
  "release_year": 2010,
  "director": "Christopher Nolan",
  "lead_actor": "Leonardo DiCaprio",
  "genre": "Science Fiction",
  "watched": true,
  "rating": 9.5
}

## 6. Add a Movie to a User's Collection

POST /users/{user_id}/collection/{external_id}

Adds a movie from the external movie database directly to a user's personal collection. Optionally accepts a watched boolean in the body.

Example response:

{ "user_id": 1042, "external_id": "tt1375666", "watched": true, "rating": null }

## 7. Update a Collection Entry

PUT /users/{user_id}/collection/{external_id}

Updates a movie entry in the user's watched list. Used to rate a film on a scale from 0 to 10 or to update watched status. Accepts optional rating and watched fields, and stores the updated tracking data in the personal database.

Example request body:

{ "rating": 9.5, "watched": true }

## 8. Remove a Movie from a User's Collection

POST /users/{user_id}/collection/{external_id}/remove

Removes a movie from the user's watched list in the personal database. This only deletes the user's saved relationship to that movie, not the movie data from the external source.

Example response:

{ "user_id": 1042, "external_id": "tt1375666", "removed": true }

## 9. Query a User's Collection

GET /users/{user_id}/collection/filter/{filter}

Returns the movies in a user's collection with filtering and sorting. Supports optional query parameters genre, director, lead_actor, release_year, min_rating, max_rating, watched, sort_by, and order.

Example response:

{
  "collection": [
    { "external_id": "tt1375666", "title": "Inception", "rating": 9.5, "release_year": 2010 }
  ]
}

## 10. Generate Collection Insights

GET /users/{user_id}/insights

Analyzes a user's saved movies and ratings to compute summary statistics and preference trends, such as favorite genres, highest-rated directors, average rating by genre, and most frequently watched release decade.

Example response:

{
  "favorite_genres": ["Science Fiction", "Thriller"],
  "top_director": "Christopher Nolan",
  "average_rating_by_genre": {
    "Science Fiction": 9.1,
    "Drama": 8.3
  },
  "most_watched_decade": "2010s"
}

## 11. Recommend Movies for a User

GET /users/{user_id}/recommendations

Uses the user's saved movies, ratings, and preferred attributes to return movie recommendations from the external movie database. 

Example response:

{
  "recommendations": [
    {
      "external_id": "tt0816692",
      "title": "Interstellar",
      "release_year": 2014,
      "director": "Christopher Nolan",
      "lead_actor": "Matthew McConaughey",
      "genre": "Science Fiction",
      "predicted_rating": 9.2
    }
  ]
}

## Complex End Point: 
    1. GET /users/{user_id}/recommendations. It computes personalized recommendations from prior ratings
    2. GET /users/{user_id}/insights` — computes cross-table analytics (favorite genres, top director/actor, top decades) from a user's watched history