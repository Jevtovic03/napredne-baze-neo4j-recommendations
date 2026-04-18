from typing import Any, Dict, List, Optional

import streamlit as st
from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

# Osnovna podesavanja konekcije ka lokalnom Neo4j instance-u.
DEFAULT_BOLT_URI = "bolt://localhost:7687"
DEFAULT_NEO4J_URI = "neo4j://localhost:7687"
DEFAULT_USER = "neo4j"
DEFAULT_PASSWORD = "password123"


@st.cache_resource
def get_driver(uri: str, user: str, password: str):
	# Kreiramo Neo4j drajver i proveravamo konekciju odmah, zbog jasne greske.
	driver = GraphDatabase.driver(uri, auth=(user, password))
	try:
		driver.verify_connectivity()
	except Exception:
		driver.close()
		raise
	return driver


def read_query(driver, query: str, params: Optional[Dict[str, Any]] = None):
	# Citamo podatke kroz sesiju koja se zatvara automatski.
	params = params or {}
	with driver.session() as session:
		result = session.run(query, **params)
		return [record.data() for record in result]


def write_query(driver, query: str, params: Optional[Dict[str, Any]] = None):
	# Upis u bazu uz pravilno zatvaranje sesije.
	params = params or {}
	with driver.session() as session:
		session.run(query, **params).consume()


def seed_data(driver) -> bool:
	# Proveravamo da li je baza prazna; ako jeste, ubacujemo inicijalne podatke.
	count_query = "MATCH (n) RETURN count(n) AS c"
	count_result = read_query(driver, count_query)
	if count_result and count_result[0]["c"] > 0:
		return False

	# (Opcionalno) jedinstvenost za brzi MERGE i cistiji graf.
	# Ako verzija Neo4j ne podrzava constraint sintaksu, nastavljamo bez toga.
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

	# Lista filmova po zanru (min. 15 ukupno).
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

	# Lista korisnika (min. 10).
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

	# MERGE korisnika i filmova.
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

	# Logicki raspored ocena da se formiraju klasteri.
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


def fetch_users(driver) -> List[str]:
	# Vracamo listu korisnika za dropdown.
	query = "MATCH (u:User) RETURN u.name AS name ORDER BY name"
	rows = read_query(driver, query)
	return [row["name"] for row in rows]


def fetch_movies(driver) -> List[str]:
	# Vracamo listu filmova za dropdown.
	query = "MATCH (m:Movie) RETURN m.title AS title ORDER BY title"
	rows = read_query(driver, query)
	return [row["title"] for row in rows]


def upsert_rating(driver, user: str, movie: str, rating: int):
	# Kreiranje ili azuriranje veze RATED sa novom ocenom.
	query = """
	MATCH (u:User {name: $user})
	MATCH (m:Movie {title: $movie})
	MERGE (u)-[r:RATED]->(m)
	SET r.rating = $rating
	"""
	write_query(driver, query, {"user": user, "movie": movie, "rating": rating})


# ---------------------------------------------------------------------------
# Veliki blok komentara za profesora o prednosti graf baze kod FOAF upita.
#
# Ovaj upit je klasican "friend of a friend" obrazac: korisnik -> film (ocena >= 4)
# -> drugi korisnici koji dele iste jake ocene -> filmovi koje ti korisnici vole.
# U SQL svetu bi to znacilo vise JOIN-ova preko jedne ili vise tabela (npr. users,
# movies, ratings) uz dodatne filtere i anti-join (da izbacimo filmove koje korisnik
# vec ima). Svaki sledeci JOIN u lancu povecava kardinalnost i moze da napravi
# eksploziju kombinacija pre nego sto se primene filteri i GROUP BY.
#
# U graf bazi, veze su prve klase i traversali prate susedstvo bez skupih spajanja
# ogromnih tabela. Neo4j koristi index-free adjacency, pa je prelazak sa cvora na
# njegove veze O(1) po grani. To znaci da se racunanje preporuka "siri" samo po
# relevantnom delu grafa (lokalno susedstvo), sto je mnogo brze od globalnih JOIN-ova.
# ---------------------------------------------------------------------------
RECOMMENDATION_QUERY = """
MATCH (u:User {name: $user})-[r1:RATED]->(m:Movie)
WHERE r1.rating >= 4
MATCH (other:User)-[r2:RATED]->(m)
WHERE r2.rating >= 4 AND other <> u
WITH DISTINCT u, other
MATCH (other)-[r3:RATED]->(rec:Movie)
WHERE r3.rating >= 4 AND NOT (u)-[:RATED]->(rec)
RETURN rec.title AS movie, count(DISTINCT other) AS score
ORDER BY score DESC, movie
"""


def fetch_recommendations(driver, user: str) -> List[Dict[str, Any]]:
	# Vracamo listu preporucenih filmova za izabranog korisnika.
	rows = read_query(driver, RECOMMENDATION_QUERY, {"user": user})
	return rows


# UI konfiguracija Streamlit aplikacije.
st.set_page_config(page_title="Movie Recommendation Engine", layout="wide")
st.title("Sistem za preporuku filmova")
st.caption("Proof of Concept za ispit 'Napredne baze podataka' (Neo4j + Streamlit)")

with st.sidebar:
	st.header("Konekcija")
	uri = st.selectbox("URI", [DEFAULT_BOLT_URI, DEFAULT_NEO4J_URI], index=0)
	user = st.text_input("User", value=DEFAULT_USER)
	password = st.text_input("Password", value=DEFAULT_PASSWORD, type="password")

try:
	driver = get_driver(uri, user, password)
except AuthError:
	st.error("Neuspesna autentifikacija. Proveri user i password.")
	st.stop()
except ServiceUnavailable:
	st.error("Neo4j servis nije dostupan. Proveri da li radi lokalni server.")
	st.stop()
except Exception as exc:
	st.error(f"Ne mogu da se povezem na Neo4j: {exc}")
	st.stop()

seeded = seed_data(driver)
if seeded:
	st.success("Baza je bila prazna i sada je inicijalno napunjena.")

users = fetch_users(driver)
movies = fetch_movies(driver)

st.divider()
st.header("1) Unos ocene")

if not users or not movies:
	st.warning("Nema korisnika ili filmova u bazi. Proveri seed.")
else:
	with st.form("rating_form"):
		selected_user = st.selectbox("Korisnik", users)
		selected_movie = st.selectbox("Film", movies)
		selected_rating = st.slider("Ocena", min_value=1, max_value=5, value=4)
		submitted = st.form_submit_button("Oceni")

	if submitted:
		upsert_rating(driver, selected_user, selected_movie, selected_rating)
		st.success("Ocena je sacuvana.")

st.divider()
st.header("2) Neo4j magija - kolaborativno filtriranje")

if not users:
	st.info("Nema korisnika za preporuku.")
else:
	rec_user = st.selectbox("Izaberi korisnika", users, key="rec_user")
	rec_rows = fetch_recommendations(driver, rec_user)

	if rec_rows:
		table_rows = [
			{"Film": row["movie"], "Broj preporuka": row["score"]}
			for row in rec_rows
		]
		st.dataframe(table_rows, width="stretch", hide_index=True)
	else:
		st.info("Trenutno nema preporuka za izabranog korisnika.")
