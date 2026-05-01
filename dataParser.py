from pathlib import Path
import json

DATA_FILE = Path("sample_movies/movies-250.json")
def parse_movies(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    movies = data.get("movies", [])

    parsed_movies = []
    for movie in movies:
        title = movie.get("Title")
        year = movie.get("Year")
        director = movie.get("Director")
        genre = movie.get("Genre")
        imdb_rating = movie.get("imdbRating")
        Actors = movie.get("Actors")
        parsed_movie = {
            "title": title,
            "year": year,
            "director": director,
            "genre": genre,
            "imdb_rating": imdb_rating,
            "Actors": Actors
        }

        parsed_movies.append(parsed_movie)
    return parsed_movies
    
def main():
    movies = parse_movies(DATA_FILE)

    print(f"Parsed {len(movies)} movies")

    for movie in movies:
        print((movie["title"],movie["year"],movie["director"],movie["Actors"],movie["genre"],movie["imdb_rating"]))


if __name__ == "__main__":
    main()