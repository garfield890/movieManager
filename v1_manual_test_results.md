# Example workflow

Priya just watched *The Shawshank Redemption* and wants to start tracking movies in Movie Manager. She creates a new user account, searches for *The Shawshank Redemption* in the movie database, adds the movie to her watched collection, rates it, and then checks her collection to confirm the saved entry.

This workflow uses the deployed Movie Manager API and the production Supabase database. It includes database-modifying endpoints because registering a user inserts a row into `users`, adding a movie inserts a row into `watched_movies`, and rating the movie updates that row.

## Testing results

### Step 1: Register a new user
1. The curl statement called:

```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "priya_watches_v2",
    "email": "priya_v2@example.com",
    "password": "testpassword123"
  }'
```  
Response:
{"user_id":2,"username":"priya_watches_v2"}% 

### Step 2: Search for Movie
```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/movies/external/search/The%20Shawshank%20Redemption/1994' \
  -H 'accept: application/json'
```
Response:
{"results":[{"movie_id":212,"title":"The Shawshank Redemption","release_year":1994,"imdb_rating":9.3}]}%    

### Step 3. Put into collection
```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/2/collection/212' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "watched": true
  }'
```
Response:
{"user_id":2,"movie_id":212,"watched":true,"rating":null}%     

### Step 4: Change rating:
```bash
curl -X 'PUT' \
  'https://moviemanager-nh3e.onrender.com/users/2/collection/212' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "watched": true,
    "rating": 9.5
  }'
```
Response:
{"user_id":2,"movie_id":212,"watched":true,"rating":9.5}% 

### Step 5: Check User Collection
```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/users/2/collection' \
  -H 'accept: application/json'
```
Response:
{"collection":[{"movie_id":212,"title":"The Shawshank Redemption","release_year":1994,"imdb_rating":9.3,"watched":true,"rating":9.5}]}%  