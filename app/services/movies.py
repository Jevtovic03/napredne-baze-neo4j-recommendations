from typing import Any, Dict, List, Optional

from app.db import read_query, write_query


def fetch_movies(driver):
    query = "MATCH (m:Movie) RETURN m.title AS title ORDER BY title"
    rows = read_query(driver, query)
    return [row["title"] for row in rows]


def fetch_genres(driver) -> List[str]:
    query = "MATCH (m:Movie) WHERE m.genre IS NOT NULL RETURN DISTINCT m.genre AS genre ORDER BY genre"
    rows = read_query(driver, query)
    return [row["genre"] for row in rows if row["genre"]]


def fetch_movie_catalog(
    driver,
    search_text: str = "",
    genre: str = "Svi",
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    min_avg_rating: Optional[float] = None,
    max_avg_rating: Optional[float] = None,
) -> List[Dict[str, Any]]:
    query = """
    MATCH (m:Movie)
    OPTIONAL MATCH (m)<-[r:RATED]-(:User)
    WITH m, avg(r.rating) AS avg_rating, count(r) AS ratings_count
    WHERE ($search_text = "" OR toLower(m.title) CONTAINS toLower($search_text))
      AND ($genre = "Svi" OR m.genre = $genre)
      AND ($min_year IS NULL OR m.year >= $min_year)
      AND ($max_year IS NULL OR m.year <= $max_year)
      AND ($min_avg_rating IS NULL OR coalesce(avg_rating, 0) >= $min_avg_rating)
      AND ($max_avg_rating IS NULL OR coalesce(avg_rating, 0) <= $max_avg_rating)
    RETURN m.title AS title,
           m.genre AS genre,
           m.year AS year,
           m.director AS director,
           coalesce(round(avg_rating * 100) / 100.0, 0.0) AS avg_rating,
           ratings_count
    ORDER BY title
    """
    return read_query(
        driver,
        query,
        {
            "search_text": search_text.strip(),
            "genre": genre,
            "min_year": min_year,
            "max_year": max_year,
            "min_avg_rating": min_avg_rating,
            "max_avg_rating": max_avg_rating,
        },
    )


def create_movie(
    driver,
    title: str,
    genre: str,
    year: int,
    director: str,
) -> bool:
    clean_title = title.strip()
    clean_genre = genre.strip()
    clean_director = director.strip()
    if not clean_title or not clean_genre or not clean_director:
        return False

    exists_query = "MATCH (m:Movie {title: $title}) RETURN count(m) AS c"
    exists_rows = read_query(driver, exists_query, {"title": clean_title})
    if exists_rows and exists_rows[0]["c"] > 0:
        return False

    query = """
    CREATE (:Movie {
        title: $title,
        genre: $genre,
        year: $year,
        director: $director
    })
    """
    write_query(
        driver,
        query,
        {
            "title": clean_title,
            "genre": clean_genre,
            "year": year,
            "director": clean_director,
        },
    )
    return True


def update_movie(
    driver,
    original_title: str,
    new_title: str,
    genre: str,
    year: int,
    director: str,
) -> bool:
    clean_new_title = new_title.strip()
    clean_genre = genre.strip()
    clean_director = director.strip()
    if not clean_new_title or not clean_genre or not clean_director:
        return False

    if clean_new_title != original_title:
        exists_query = "MATCH (m:Movie {title: $title}) RETURN count(m) AS c"
        exists_rows = read_query(driver, exists_query, {"title": clean_new_title})
        if exists_rows and exists_rows[0]["c"] > 0:
            return False

    query = """
    MATCH (m:Movie {title: $original_title})
    SET m.title = $new_title,
        m.genre = $genre,
        m.year = $year,
        m.director = $director
    RETURN count(m) AS updated
    """
    rows = read_query(
        driver,
        query,
        {
            "original_title": original_title,
            "new_title": clean_new_title,
            "genre": clean_genre,
            "year": year,
            "director": clean_director,
        },
    )
    return bool(rows and rows[0]["updated"] == 1)


def delete_movie(driver, title: str) -> bool:
    query = """
    MATCH (m:Movie {title: $title})
    DETACH DELETE m
    RETURN count(*) AS deleted
    """
    rows = read_query(driver, query, {"title": title})
    return bool(rows and rows[0]["deleted"] == 1)
