from typing import Any, Dict, List

from app.db import read_query


def fetch_user_profile_summary(driver, user: str) -> Dict[str, Any]:
    query = """
    MATCH (u:User {name: $user})
    OPTIONAL MATCH (u)-[r:RATED]->(m:Movie)
    WITH u, count(r) AS ratings_count, avg(r.rating) AS avg_rating
    OPTIONAL MATCH (u)-[rg:RATED]->(mg:Movie)
    WHERE rg.rating >= 4 AND mg.genre IS NOT NULL
    WITH ratings_count,
         avg_rating,
         collect(mg.genre) AS liked_genres
    UNWIND liked_genres AS genre
    WITH ratings_count,
         avg_rating,
         genre,
         count(*) AS genre_count
    ORDER BY genre_count DESC, genre
    RETURN ratings_count,
           coalesce(round(avg_rating * 100) / 100.0, 0.0) AS avg_rating,
           collect({genre: genre, count: genre_count})[0..3] AS favorite_genres
    """
    rows = read_query(driver, query, {"user": user})
    if not rows:
        return {"ratings_count": 0, "avg_rating": 0.0, "favorite_genres": []}

    row = rows[0]
    return {
        "ratings_count": row["ratings_count"],
        "avg_rating": row["avg_rating"],
        "favorite_genres": row["favorite_genres"],
    }


def fetch_recent_ratings_for_user(driver, user: str, limit: int = 5) -> List[Dict[str, Any]]:
    query = """
    MATCH (:User {name: $user})-[r:RATED]->(m:Movie)
    RETURN m.title AS movie,
           m.genre AS genre,
           m.year AS year,
           r.rating AS rating
    ORDER BY r.rating DESC, movie
    LIMIT $limit
    """
    return read_query(driver, query, {"user": user, "limit": limit})
