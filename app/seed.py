from app.db import read_query, write_query


def seed_data(driver) -> bool:
    count_query = "MATCH (n) RETURN count(n) AS c"
    count_result = read_query(driver, count_query)
    is_empty = not (count_result and count_result[0]["c"] > 0)

    try:
        write_query(
            driver,
            "CREATE CONSTRAINT user_name_unique IF NOT EXISTS FOR (u:User) REQUIRE u.name IS UNIQUE",
        )
        write_query(
            driver,
            "CREATE CONSTRAINT movie_title_unique IF NOT EXISTS FOR (m:Movie) REQUIRE m.title IS UNIQUE",
        )
    except Exception:
        pass

    movies = [
        {
            "title": "The Matrix",
            "genre": "Sci-Fi",
            "year": 1999,
            "director": "Lana Wachowski, Lilly Wachowski",
            "poster_url": "https://m.media-amazon.com/images/M/MV5BNzQzOTk3NTAt.jpg",
        },
        {
            "title": "Inception",
            "genre": "Sci-Fi",
            "year": 2010,
            "director": "Christopher Nolan",
            "poster_url": "https://m.media-amazon.com/images/M/MV5BMmEzNTYxZTQt.jpg",
        },
        {
            "title": "Interstellar",
            "genre": "Sci-Fi",
            "year": 2014,
            "director": "Christopher Nolan",
            "poster_url": "https://m.media-amazon.com/images/M/MV5BZjdkOTU3MDAt.jpg",
        },
        {
            "title": "Blade Runner 2049",
            "genre": "Sci-Fi",
            "year": 2017,
            "director": "Denis Villeneuve",
            "poster_url": "https://m.media-amazon.com/images/M/MV5BMTE5OTc4MTM5N15.jpg",
        },
        {
            "title": "Arrival",
            "genre": "Sci-Fi",
            "year": 2016,
            "director": "Denis Villeneuve",
            "poster_url": "https://m.media-amazon.com/images/M/MV5BMTQyOTIwNTYwNl5.jpg",
        },
        {
            "title": "Mad Max: Fury Road",
            "genre": "Action",
            "year": 2015,
            "director": "George Miller",
            "poster_url": "https://m.media-amazon.com/images/M/MV5BNzY4OTI1NDUzMV5.jpg",
        },
        {
            "title": "John Wick",
            "genre": "Action",
            "year": 2014,
            "director": "Chad Stahelski",
            "poster_url": "https://m.media-amazon.com/images/M/MV5BODQyNWQzMzAt.jpg",
        },
        {
            "title": "Die Hard",
            "genre": "Action",
            "year": 1988,
            "director": "John McTiernan",
            "poster_url": "https://m.media-amazon.com/images/M/MV5BYjdlYmQ3MWYt.jpg",
        },
        {
            "title": "The Dark Knight",
            "genre": "Action",
            "year": 2008,
            "director": "Christopher Nolan",
            "poster_url": "https://m.media-amazon.com/images/M/MV5BMTMxNTMwODAxNV5.jpg",
        },
        {
            "title": "Gladiator",
            "genre": "Action",
            "year": 2000,
            "director": "Ridley Scott",
            "poster_url": "https://m.media-amazon.com/images/M/MV5BMDliMmE4YTct.jpg",
        },
        {
            "title": "The Shawshank Redemption",
            "genre": "Drama",
            "year": 1994,
            "director": "Frank Darabont",
            "poster_url": "https://m.media-amazon.com/images/M/MV5BNDE3ODcxYzMt.jpg",
        },
        {
            "title": "Forrest Gump",
            "genre": "Drama",
            "year": 1994,
            "director": "Robert Zemeckis",
            "poster_url": "https://m.media-amazon.com/images/M/MV5BNWIwODNlNzUt.jpg",
        },
        {
            "title": "Fight Club",
            "genre": "Drama",
            "year": 1999,
            "director": "David Fincher",
            "poster_url": "https://m.media-amazon.com/images/M/MV5BMmEzMDYxMTYt.jpg",
        },
        {
            "title": "The Godfather",
            "genre": "Drama",
            "year": 1972,
            "director": "Francis Ford Coppola",
            "poster_url": "https://m.media-amazon.com/images/M/MV5BY2Q4Y2VmNWEt.jpg",
        },
        {
            "title": "Parasite",
            "genre": "Drama",
            "year": 2019,
            "director": "Bong Joon Ho",
            "poster_url": "https://m.media-amazon.com/images/M/MV5BZjE0NWQzZDMt.jpg",
        },
    ]

    write_query(
        driver,
        """
        UNWIND $movies AS movie
        MERGE (m:Movie {title: movie.title})
        SET m.genre = movie.genre,
            m.year = movie.year,
            m.director = movie.director
        """,
        {"movies": movies},
    )

    if not is_empty:
        return False

    users = [
        "Ana",
        "Boris",
        "Ceda",
        "Dina",
        "Ema",
        "Filip",
        "Goran",
        "Hana",
        "Ivan",
        "Jelena",
    ]

    write_query(
        driver,
        "UNWIND $users AS name MERGE (:User {name: name})",
        {"users": users},
    )

    ratings_by_user = {
        "Ana": [
            ("The Matrix", 5),
            ("Inception", 5),
            ("Interstellar", 4),
            ("Arrival", 4),
            ("Blade Runner 2049", 4),
            ("The Dark Knight", 3),
            ("Fight Club", 3),
        ],
        "Boris": [
            ("The Matrix", 5),
            ("Interstellar", 5),
            ("Inception", 4),
            ("Arrival", 4),
            ("Blade Runner 2049", 4),
            ("John Wick", 3),
        ],
        "Ceda": [
            ("Inception", 5),
            ("Interstellar", 4),
            ("Arrival", 4),
            ("Blade Runner 2049", 4),
            ("Gladiator", 3),
        ],
        "Dina": [
            ("Mad Max: Fury Road", 5),
            ("John Wick", 5),
            ("Die Hard", 4),
            ("The Dark Knight", 5),
            ("Gladiator", 4),
            ("The Matrix", 3),
        ],
        "Ema": [
            ("John Wick", 5),
            ("Mad Max: Fury Road", 4),
            ("Die Hard", 4),
            ("The Dark Knight", 4),
            ("Gladiator", 4),
            ("Inception", 3),
        ],
        "Filip": [
            ("The Shawshank Redemption", 5),
            ("The Godfather", 5),
            ("Forrest Gump", 4),
            ("Fight Club", 4),
            ("Parasite", 4),
            ("Gladiator", 3),
        ],
        "Goran": [
            ("The Godfather", 5),
            ("The Shawshank Redemption", 4),
            ("Fight Club", 5),
            ("Parasite", 4),
            ("Forrest Gump", 4),
            ("The Dark Knight", 3),
        ],
        "Hana": [
            ("The Matrix", 4),
            ("Inception", 4),
            ("Arrival", 4),
            ("The Shawshank Redemption", 4),
            ("Parasite", 4),
            ("John Wick", 3),
        ],
        "Ivan": [
            ("Mad Max: Fury Road", 4),
            ("John Wick", 4),
            ("The Dark Knight", 4),
            ("Inception", 4),
            ("Interstellar", 4),
            ("Forrest Gump", 3),
        ],
        "Jelena": [
            ("The Shawshank Redemption", 4),
            ("Forrest Gump", 4),
            ("The Godfather", 4),
            ("Gladiator", 4),
            ("Die Hard", 4),
            ("Arrival", 3),
        ],
    }

    ratings = []
    for user, items in ratings_by_user.items():
        for movie, rating in items:
            ratings.append({"user": user, "movie": movie, "rating": rating})

    write_query(
        driver,
        """
        UNWIND $ratings AS r
        MATCH (u:User {name: r.user})
        MATCH (m:Movie {title: r.movie})
        MERGE (u)-[rel:RATED]->(m)
        SET rel.rating = r.rating
        """,
        {"ratings": ratings},
    )

    return True
