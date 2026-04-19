from app.db import read_query, write_query


def seed_data(driver) -> bool:
    count_query = "MATCH (n) RETURN count(n) AS c"
    count_result = read_query(driver, count_query)
    if count_result and count_result[0]["c"] > 0:
        return False

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

    scifi_movies = [
        "The Matrix",
        "Inception",
        "Interstellar",
        "Blade Runner 2049",
        "Arrival",
    ]
    action_movies = [
        "Mad Max: Fury Road",
        "John Wick",
        "Die Hard",
        "The Dark Knight",
        "Gladiator",
    ]
    drama_movies = [
        "The Shawshank Redemption",
        "Forrest Gump",
        "Fight Club",
        "The Godfather",
        "Parasite",
    ]

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
    write_query(
        driver,
        "UNWIND $movies AS title MERGE (:Movie {title: title})",
        {"movies": scifi_movies + action_movies + drama_movies},
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
