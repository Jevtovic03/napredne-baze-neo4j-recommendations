from app.db import read_query, write_query


def fetch_users(driver):
    query = "MATCH (u:User) RETURN u.name AS name ORDER BY name"
    rows = read_query(driver, query)
    return [row["name"] for row in rows]


def create_user(driver, name: str) -> bool:
    clean_name = name.strip()
    if not clean_name:
        return False

    exists_query = "MATCH (u:User {name: $name}) RETURN count(u) AS c"
    exists_rows = read_query(driver, exists_query, {"name": clean_name})
    if exists_rows and exists_rows[0]["c"] > 0:
        return False

    create_query = "CREATE (:User {name: $name})"
    write_query(driver, create_query, {"name": clean_name})
    return True
