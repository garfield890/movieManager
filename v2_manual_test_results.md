# Example Flow 2

Marcus wants to recommend a new film to his partner tonight, but first he needs to finish rating *Interstellar*, which he watched last week.

He registers and logs in to Movie Manager, adds *Interstellar* with a rating of `8.5`, adds *Inception* with a rating of `9.1`, adds *The Matrix* with a rating of `9.0`, adds *Star Wars: Episode V - The Empire Strikes Back* with a rating of `8.4`, checks his sci-fi movies to see how they rank inside his collection, and then asks the API for personalized recommendations. He sees that he doesn't have enough movies to get personalized recommendations, so he adds *Fight Club* with a rating of `8.1`. He asks the API for personalized recommendations again to choose a film he can recommend to his partner. 

## Testing Results

### Step 1: Register A New User

```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "marcus",
  "email": "marcus@testing.com",
  "password": "testing123"
}'
```
Response:
{"user_id": 5, "username": "marcus"}

### Step 2: Login User

```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/login' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "marcus",
  "password": "testing123"
}'
```
Response:
{"user_id": 5, "username": "marcus", "token": "v1-demo-token-5"}

### Step 3: Search for Interstellar, Inception, The Matrix, Empire Strikes Back

```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/movies/external/search/Interstellar/2014' \
  -H 'accept: application/json' \
```
Response:
{
  "results": [
    {
      "movie_id": 239,
      "title": "Interstellar",
      "release_year": 2014,
      "imdb_rating": 8.7
    }
  ]
}

```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/movies/external/search/Inception/2010' \
  -H 'accept: application/json' \
```
Response:
{
  "results": [
    {
      "movie_id": 224,
      "title": "Inception",
      "release_year": 2010,
      "imdb_rating": 8.8
    }
  ]
}

```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/movies/external/search/The%20Matrix/1999' \
  -H 'accept: application/json' \
```
Response:
{
  "results": [
    {
      "movie_id": 227,
      "title": "The Matrix",
      "release_year": 1999,
      "imdb_rating": 8.7
    }
  ]
}

```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/movies/external/search/tar%20Wars%3A%20Episode%20V%20-%20The%20Empire%20Strikes%20Back/1980' \
  -H 'accept: application/json' \
```
Response:
{
  "results": [
    {
      "movie_id": 226,
      "title": "Star Wars: Episode V - The Empire Strikes Back",
      "release_year": 1980,
      "imdb_rating": 8.7
    }
  ]
}

### Step 4: Add Interstellar, Inception, The Matrix, Empire Strikes Back

```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/5/collection/239' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true
}'
```
Response:
{"user_id": 5, "movie_id": 239, "watched": true, "rating": null}

```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/5/collection/224' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true
}'
```
Response:
{"user_id": 5, "movie_id": 224, "watched": true, "rating": null}

```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/5/collection/227' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true
}'
```
Response:
{"user_id": 5, "movie_id": 227, "watched": true, "rating": null}

```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/5/collection/226' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true
}'
```
Response:
{"user_id": 5, "movie_id": 226, "watched": true, "rating": null}

### Step 5: Enter Movie Ratings

```bash
curl -X 'PUT' \
  'https://moviemanager-nh3e.onrender.com/users/5/collection/239' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true,
  "rating": 8.5
}'
```
Response:
{"user_id": 5, "movie_id": 239, "watched": true, "rating": 8.5}

```bash
curl -X 'PUT' \
  'https://moviemanager-nh3e.onrender.com/users/5/collection/224' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true,
  "rating": 9.1
}'
```
Response:
{"user_id": 5, "movie_id": 224, "watched": true, "rating": 9.1}

```bash
curl -X 'PUT' \
  'https://moviemanager-nh3e.onrender.com/users/5/collection/227' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true,
  "rating": 9.0
}'
```
Response:
{"user_id": 5, "movie_id": 227, "watched": true,"rating": 9}

```bash
curl -X 'PUT' \
  'https://moviemanager-nh3e.onrender.com/users/5/collection/226' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true,
  "rating": 8.4
}'
```
Response:
{"user_id": 5, "movie_id": 226, "watched": true, "rating": 8.4}

### Step 6: Filter by Genre - Sci-Fi

```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/users/5/collection/filter/genre/sci-fi' \
  -H 'accept: application/json' \
```
Response:
{
  "collection": [
    {
      "movie_id": 224,
      "movie_title": "Inception",
      "release_year": 2010,
      "rating": 9.1,
      "genre": "Sci-Fi"
    },
    {
      "movie_id": 227,
      "movie_title": "The Matrix",
      "release_year": 1999,
      "rating": 9,
      "genre": "Sci-Fi"
    },
    {
      "movie_id": 239,
      "movie_title": "Interstellar",
      "release_year": 2014,
      "rating": 8.5,
      "genre": "Sci-Fi"
    }
  ]
}

### Step 7: Get Movie Recommendations

```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/users/5/recommendations' \
  -H 'accept: application/json' \
```
Response:
{
  "description": "Not enough movies watched to provide personalized recommendations. Here are the top unwatched movies.",
  "collection": [
    {
      "movie_id": 212,
      "movie_name": "The Shawshank Redemption",
      "release_year": 1994,
      "imdb_rating": 9.3
    },
    {
      "movie_id": 213,
      "movie_name": "The Godfather",
      "release_year": 1972,
      "imdb_rating": 9.2
    },
    {
      "movie_id": 214,
      "movie_name": "The Dark Knight",
      "release_year": 2008,
      "imdb_rating": 9.1
    },
    {
      "movie_id": 216,
      "movie_name": "12 Angry Men",
      "release_year": 1957,
      "imdb_rating": 9
    },
    {
      "movie_id": 215,
      "movie_name": "The Godfather: Part II",
      "release_year": 1974,
      "imdb_rating": 9
    }
  ]
}

### Step 8: Search for Fight Club to Add It

```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/movies/external/search/Fight%20Club/1999' \
  -H 'accept: application/json' \
```
Response:
{
  "results": [
    {
      "movie_id": 223,
      "title": "Fight Club",
      "release_year": 1999,
      "imdb_rating": 8.8
    }
  ]
}

### Step 9: Add Fight Club to Watched Movies, then Rate It `8.1`

```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/5/collection/223' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true
}'
```
Response:
{"user_id": 5, "movie_id": 223, "watched": true, "rating": null}

```bash
curl -X 'PUT' \
  'https://moviemanager-nh3e.onrender.com/users/5/collection/223' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true,
  "rating": 8.1
}'
```
Response: 
{"user_id": 5, "movie_id": 223, "watched": true, "rating": 8.1}

### Step 9: Get Movie Recommendations Again

```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/users/5/recommendations' \
  -H 'accept: application/json' \
```
Response:
{
  "description": "Your Top 5 Recommended Movies",
  "collection": [
    {
      "movie_id": 240,
      "movie_name": "Terminator 2: Judgment Day",
      "release_year": 1991,
      "imdb_rating": 8.6,
      "genre": "Sci-Fi",
      "predicted_rating": 8.866666666666667
    },
    {
      "movie_id": 241,
      "movie_name": "Back to the Future",
      "release_year": 1985,
      "imdb_rating": 8.6,
      "genre": "Sci-Fi",
      "predicted_rating": 8.866666666666667
    },
    {
      "movie_id": 260,
      "movie_name": "Alien",
      "release_year": 1979,
      "imdb_rating": 8.5,
      "genre": "Sci-Fi",
      "predicted_rating": 8.866666666666667
    },
    {
      "movie_id": 276,
      "movie_name": "Aliens",
      "release_year": 1986,
      "imdb_rating": 8.4,
      "genre": "Sci-Fi",
      "predicted_rating": 8.866666666666667
    },
    {
      "movie_id": 274,
      "movie_name": "Avengers: Infinity War",
      "release_year": 2018,
      "imdb_rating": 8.4,
      "genre": "Sci-Fi",
      "predicted_rating": 8.866666666666667
    }
  ]
}

*Based on this, Marcus would choose Terminator 2: Judgement Day to recommend to his partner.*

# Example Flow 3

Lina has been on a Quentin Tarantino kick and wants to clean up her library: add *Pulp Fiction*, add *Django: Unchained*, add *Inglourious Basterds*, add *Reservoir Dogs*, remove *Django: Unchained*, and check the end result.

She logs in to Movie Manager, searches for each of those Quentin Tarantino films, adds them to her collection, marks them as watched, and rates them. Then she removes *Django: Unchained* from her collection and filters her library by director to confirm that her Quentin Tarantino shelf now reflects the movies she wants to keep.

She finishes by calling the insights endpoint to see what her watched list says about her tastes, including her favorite genres, top director, top actor, and most-watched decades.

## Testing Results

### Step 1: Register a New User

```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "lina",
  "email": "lina@testing.com",
  "password": "testing1234"
}'
```
Response:
{"user_id": 6, "username": "lina"}

### Step 2: Login User

```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/login' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "lina",
  "password": "testing1234"
}'
```
Response:
{"user_id": 6, "username": "lina", "token": "v1-demo-token-6"}

### Step 3: Search for Quentin Tarantino Films

```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/movies/external/search/Pulp%20Fiction/1994' \
  -H 'accept: application/json' \
```
Response:
{
  "results": [
    {
      "movie_id": 219,
      "title": "Pulp Fiction",
      "release_year": 1994,
      "imdb_rating": 8.9
    }
  ]
}

```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/movies/external/search/Django%20Unchained/2012' \
  -H 'accept: application/json' \
```
Response:
{
  "results": [
    {
      "movie_id": 267,
      "title": "Django Unchained",
      "release_year": 2012,
      "imdb_rating": 8.4
    }
  ]
}

```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/movies/external/search/Reservoir%20Dogs/1992' \
  -H 'accept: application/json' \
```
Response:
{
  "results": [
    {
      "movie_id": 300,
      "title": "Reservoir Dogs",
      "release_year": 1992,
      "imdb_rating": 8.3
    }
  ]
}

```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/movies/external/search/Inglourious%20Basterds/2009' \
  -H 'accept: application/json' \
```
Response:
{
  "results": [
    {
      "movie_id": 288,
      "title": "Inglourious Basterds",
      "release_year": 2009,
      "imdb_rating": 8.3
    }
  ]
}

### Step 4: Add These Quentin Tarantino Films and Rate Them All 9.6

```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/6/collection/219' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true
}'
```
Response:
{"user_id": 6, "movie_id": 219, "watched": true, "rating": null}

```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/6/collection/267' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true
}'
```
Response:
{"user_id": 6, "movie_id": 267, "watched": true, "rating": null}

```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/6/collection/288' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true
}'
```
Response: 
{"user_id": 6, "movie_id": 288, "watched": true, "rating": null}

```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/6/collection/300' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true
}'
```
Response:
{"user_id": 6, "movie_id": 300, "watched": true, "rating": null}

```bash
curl -X 'PUT' \
  'https://moviemanager-nh3e.onrender.com/users/6/collection/219' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true,
  "rating": 9.1
}'
```
Response:
{"user_id": 6, "movie_id": 219, "watched": true, "rating": 9.6}

```bash
curl -X 'PUT' \
  'https://moviemanager-nh3e.onrender.com/users/6/collection/267' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true,
  "rating": 9.6
}'
```
Response:
{"user_id": 6, "movie_id": 267, "watched": true, "rating": 9.6}

```bash
curl -X 'PUT' \
  'https://moviemanager-nh3e.onrender.com/users/6/collection/288' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true,
  "rating": 9.6
}'
```
Response:
{"user_id": 6, "movie_id": 288, "watched": true, "rating": 9.6}

```bash
curl -X 'PUT' \
  'https://moviemanager-nh3e.onrender.com/users/6/collection/300' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "watched": true,
  "rating": 9.6
}'
```
Response:
{
  "user_id": 6,
  "movie_id": 300,
  "watched": true,
  "rating": 9.6
}

### Step 5: Remove Django Unchained

```bash
curl -X 'POST' \
  'https://moviemanager-nh3e.onrender.com/users/6/collection/267/remove' \
  -H 'accept: application/json' \
  -d ''
```
Response:
{"user_id": 6, "movie_name": "Django Unchained", "removed": true}

### Step 6: Filter by Director (Quentin Tarantino)

```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/users/6/collection/filter/director/quentin_tarantino' \
  -H 'accept: application/json' \
```
Response:
{
  "collection": [
    {
      "movie_id": 219,
      "movie_title": "Pulp Fiction",
      "release_year": 1994,
      "rating": 9.6,
      "director": "Quentin Tarantino"
    },
    {
      "movie_id": 288,
      "movie_title": "Inglourious Basterds",
      "release_year": 2009,
      "rating": 9.6,
      "director": "Quentin Tarantino"
    },
    {
      "movie_id": 300,
      "movie_title": "Reservoir Dogs",
      "release_year": 1992,
      "rating": 9.6,
      "director": "Quentin Tarantino"
    }
  ]
}

### Step 7: Get User's Movie Insights

```bash
curl -X 'GET' \
  'https://moviemanager-nh3e.onrender.com/users/6/insights' \
  -H 'accept: application/json' \
```
Response:
{
  "favorite_genres": [
    "Drama",
    "Crime",
    "War"
  ],
  "top_director": {
    "name": "Quentin Tarantino",
    "watch_count": 3
  },
  "top_actor": {
    "actor_name": "Diane Kruger",
    "watch_count": 1
  },
  "top_decade": [
    "1990s",
    "2000s"
  ]
}