# Example workflow

Priya just watched Shawshank Redemption and wants to start tracking movies in Movie Manager. She creates a new user account, searches for Shawshank redemption in the movie database, adds the movie to her watched collection, rates it, and then checks her collection to confirm the saved entry.

This workflow uses the deployed Movie Manager API and the production Supabase database. It includes database-modifying endpoints because registering a user inserts a row into `users`, adding a movie inserts a row into `watched_movies`, and rating the movie updates that row.

# Testing results

## Step 1: Register a new user

1. The curl statement called:

```bash
curl -X 'POST' \
  'https://YOUR-RENDER-URL/users/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "priya_watches",
    "email": "priya@example.com",
    "password": "testpassword123"
  }'
response : {
  "user_id": 1,
  "username": "priya_watches"
}

2. PUT /users/{user_id}/collection/{movie_id}, put into collection

curl -X 'PUT' \
  'http://127.0.0.1:8000/users/1/collection/212' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true,
  "rating": 10
}'
response:
{
  "user_id": 1,
  "movie_id": 212,
  "watched": true,
  "rating": 10
}

3.Check User Collection
curl -X 'GET' \
  'http://127.0.0.1:8000/users/1/collection' \
  -H 'accept: application/json'
response:
{
  "collection": [
    {
      "movie_id": 212,
      "title": "The Shawshank Redemption",
      "release_year": 1994,
      "imdb_rating": 9.3,
      "watched": true,
      "rating": 10
    }
  ]
}