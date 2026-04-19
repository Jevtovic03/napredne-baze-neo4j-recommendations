from app.db import read_query


def fetch_movies(driver):
    query = "MATCH (m:Movie) RETURN m.title AS title ORDER BY title"
    rows = read_query(driver, query)
    return [row["title"] for row in rows]
