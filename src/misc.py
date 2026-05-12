from decimal import Decimal

GENRE_ALIASES = {
    # Drama
    "drama": "Drama",
    "dramatic": "Drama",

    # Crime
    "crime": "Crime",
    "criminal": "Crime",
    "gangster": "Crime",
    "mob": "Crime",
    "mafia": "Crime",

    # Action
    "action": "Action",
    "action movie": "Action",
    "action films": "Action",

    # Biography
    "biography": "Biography",
    "biopic": "Biography",
    "bio": "Biography",

    # History
    "history": "History",
    "historical": "History",
    "period history": "History",

    # Adventure
    "adventure": "Adventure",
    "adventures": "Adventure",
    "quest": "Adventure",

    # Western
    "western": "Western",
    "westerns": "Western",
    "cowboy": "Western",
    "cowboys": "Western",

    # Romance
    "romance": "Romance",
    "romantic": "Romance",
    "love story": "Romance",
    "rom com": "Romance",
    "romcom": "Romance",
    "romantic comedy": "Romance",

    # Sci-Fi
    "sci fi": "Sci-Fi",
    "scifi": "Sci-Fi",
    "sci-fi": "Sci-Fi",
    "science fiction": "Sci-Fi",
    "science-fiction": "Sci-Fi",
    "sf": "Sci-Fi",

    # Fantasy
    "fantasy": "Fantasy",
    "fantastical": "Fantasy",
    "magic": "Fantasy",
    "magical": "Fantasy",

    # Mystery
    "mystery": "Mystery",
    "mysteries": "Mystery",
    "detective": "Mystery",
    "whodunit": "Mystery",

    # Family
    "family": "Family",
    "kids": "Family",
    "children": "Family",
    "children's": "Family",
    "childrens": "Family",
    "family friendly": "Family",

    # Thriller
    "thriller": "Thriller",
    "thrillers": "Thriller",
    "suspense": "Thriller",
    "suspenseful": "Thriller",

    # War
    "war": "War",
    "warfare": "War",
    "military": "War",
    "battle": "War",

    # Comedy
    "comedy": "Comedy",
    "comedies": "Comedy",
    "funny": "Comedy",
    "humor": "Comedy",
    "humorous": "Comedy",

    # Animation
    "animation": "Animation",
    "animated": "Animation",
    "cartoon": "Animation",
    "cartoons": "Animation",
    "anime": "Animation",

    # Horror
    "horror": "Horror",
    "scary": "Horror",
    "frightening": "Horror",
    "slasher": "Horror",

    # Musical
    "musical": "Musical",
    "musicals": "Musical",
    "song and dance": "Musical",
    
    # Film-Noir
    "film noir": "Film-Noir",
    "film-noir": "Film-Noir",
    "noir": "Film-Noir",

    # Music
    "music": "Music",
    "musician": "Music",
    "concert": "Music",
    "band": "Music",

    # Sport
    "sport": "Sport",
    "sports": "Sport",
    "athletics": "Sport",
    "athletic": "Sport",
    "competition": "Sport",
}

def decimal_to_float(value):
    if value is None:
        return None

    if isinstance(value, Decimal):
        return float(value)

    return value

def normalize_person(value: str) -> str:
    return " ".join(
        part.capitalize()
        for part in value.strip().replace("_", " ").replace("-", " ").split()
    )