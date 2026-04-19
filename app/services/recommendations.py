from typing import Any, Dict, List

from app.db import read_query

RECOMMENDATION_QUERY = """
MATCH (u:User {name: $user})-[r1:RATED]->(m:Movie)
WHERE r1.rating >= $threshold
MATCH (other:User)-[r2:RATED]->(m)
WHERE r2.rating >= $threshold AND other <> u
WITH DISTINCT u, other
MATCH (other)-[r3:RATED]->(rec:Movie)
WHERE r3.rating >= $threshold AND NOT (u)-[:RATED]->(rec)
RETURN rec.title AS movie, count(DISTINCT other) AS score
ORDER BY score DESC, movie
"""


def fetch_recommendations(driver, user: str, threshold: int) -> List[Dict[str, Any]]:
    return read_query(driver, RECOMMENDATION_QUERY, {"user": user, "threshold": threshold})
