from typing import Any, Dict, List

from app.db import read_query


def create_rating(driver, user: str, movie: str, rating: int) -> bool:
    query = """
    MATCH (u:User {name: $user})
    MATCH (m:Movie {title: $movie})
    OPTIONAL MATCH (u)-[existing:RATED]->(m)
    WITH u, m, existing
    WHERE existing IS NULL
    CREATE (u)-[:RATED {rating: $rating}]->(m)
    RETURN count(*) AS created
    """
    rows = read_query(driver, query, {"user": user, "movie": movie, "rating": rating})
    return bool(rows and rows[0]["created"] == 1)


def fetch_ratings_for_user(driver, user: str) -> List[Dict[str, Any]]:
    query = """
    MATCH (:User {name: $user})-[r:RATED]->(m:Movie)
    RETURN m.title AS movie, r.rating AS rating
    ORDER BY movie
    """
    return read_query(driver, query, {"user": user})


def fetch_rated_movies_for_user(driver, user: str) -> List[str]:
    query = """
    MATCH (:User {name: $user})-[r:RATED]->(m:Movie)
    RETURN m.title AS movie
    ORDER BY movie
    """
    rows = read_query(driver, query, {"user": user})
    return [row["movie"] for row in rows]


def update_rating(driver, user: str, movie: str, rating: int) -> bool:
    query = """
    MATCH (:User {name: $user})-[r:RATED]->(:Movie {title: $movie})
    SET r.rating = $rating
    RETURN count(r) AS updated
    """
    rows = read_query(driver, query, {"user": user, "movie": movie, "rating": rating})
    return bool(rows and rows[0]["updated"] == 1)


def delete_rating(driver, user: str, movie: str) -> bool:
    query = """
    MATCH (:User {name: $user})-[r:RATED]->(:Movie {title: $movie})
    DELETE r
    RETURN count(*) AS deleted
    """
    rows = read_query(driver, query, {"user": user, "movie": movie})
    return bool(rows and rows[0]["deleted"] == 1)
