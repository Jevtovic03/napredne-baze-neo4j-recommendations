import streamlit as st
from neo4j.exceptions import AuthError, ServiceUnavailable
from app.config import (
    DEFAULT_BOLT_URI,
    DEFAULT_PASSWORD,
    DEFAULT_USER,
)
from app.db import get_driver
from app.seed import seed_data
from app.services.movies import (
    create_movie,
    delete_movie,
    fetch_genres,
    fetch_movie_catalog,
    fetch_movies,
    update_movie,
)
from app.services.profiles import fetch_recent_ratings_for_user, fetch_user_profile_summary
from app.services.ratings import (
    create_rating,
    delete_rating,
    fetch_rated_movies_for_user,
    fetch_ratings_for_user,
    update_rating,
)
from app.services.recommendations import fetch_recommendations
from app.services.users import create_user, fetch_users


def render_connection_sidebar():
    with st.sidebar:
        st.header("Konekcija")
        user = st.text_input("User", value=DEFAULT_USER)
        password = st.text_input("Password", value=DEFAULT_PASSWORD, type="password")
    return DEFAULT_BOLT_URI, user, password


def render_user_creation(driver):
    st.header("1) Dodavanje novog korisnika")
    with st.form("create_user_form", clear_on_submit=True):
        new_user_name = st.text_input("Ime novog korisnika")
        submitted = st.form_submit_button("Dodaj korisnika")

    if submitted:
        if create_user(driver, new_user_name):
            st.success("Korisnik je uspesno dodat.")
            st.rerun()
        else:
            st.info("Korisnik vec postoji ili ime nije validno.")


def render_rating_crud(driver, users, movies):
    st.header("3) Izmene ocena")

    if not users or not movies:
        st.warning("Nema korisnika ili filmova u bazi.")
        return

    create_tab, read_tab, update_tab, delete_tab = st.tabs(
        ["Oceni", "Vidi ocene", "Promeni ocenu", "Obrisi ocenu"]
    )

    with create_tab:
        with st.form("create_rating_form"):
            create_user_name = st.selectbox("Korisnik", users, key="create_user")
            create_movie_title = st.selectbox("Film", movies, key="create_movie")
            create_rating_value = st.slider(
                "Ocena", min_value=1, max_value=5, value=4, key="create_rating_value"
            )
            create_submitted = st.form_submit_button("Sacuvaj novu recenziju")

        if create_submitted:
            created = create_rating(driver, create_user_name, create_movie_title, create_rating_value)
            if created:
                st.success("Recenzija je kreirana.")
                st.rerun()
            else:
                st.warning("Recenzija vec postoji za ovog korisnika i film.")

    with read_tab:
        read_user_name = st.selectbox("Korisnik", users, key="read_user")
        rows = fetch_ratings_for_user(driver, read_user_name)
        if rows:
            table_rows = [{"Film": row["movie"], "Ocena": row["rating"]} for row in rows]
            st.dataframe(table_rows, width="stretch", hide_index=True)
        else:
            st.info("Korisnik jos nema recenzija.")

    with update_tab:
        update_user_name = st.selectbox("Korisnik", users, key="update_user")
        update_movies = fetch_rated_movies_for_user(driver, update_user_name)
        if not update_movies:
            st.info("Nema recenzija za azuriranje.")
        else:
            with st.form("update_rating_form"):
                update_movie_title = st.selectbox("Film", update_movies, key="update_movie")
                update_rating_value = st.slider(
                    "Nova ocena",
                    min_value=1,
                    max_value=5,
                    value=4,
                    key="update_rating_value",
                )
                update_submitted = st.form_submit_button("Azuriraj recenziju")

            if update_submitted:
                updated = update_rating(
                    driver,
                    update_user_name,
                    update_movie_title,
                    update_rating_value,
                )
                if updated:
                    st.success("Recenzija je azurirana.")
                    st.rerun()
                else:
                    st.error("Azuriranje nije uspelo.")

    with delete_tab:
        delete_user_name = st.selectbox("Korisnik", users, key="delete_user")
        delete_movies = fetch_rated_movies_for_user(driver, delete_user_name)
        if not delete_movies:
            st.info("Nema recenzija za brisanje.")
        else:
            with st.form("delete_rating_form"):
                delete_movie_title = st.selectbox("Film", delete_movies, key="delete_movie")
                delete_submitted = st.form_submit_button("Obrisi recenziju")

            if delete_submitted:
                deleted = delete_rating(driver, delete_user_name, delete_movie_title)
                if deleted:
                    st.success("Recenzija je obrisana.")
                    st.rerun()
                else:
                    st.error("Brisanje nije uspelo.")


def render_movie_management(driver):
    st.header("2) Filmovi: CRUD + pretraga")

    search_tab, create_tab, update_tab, delete_tab = st.tabs(
        ["Pretraga i filteri", "Dodaj film", "Izmeni film", "Obrisi film"]
    )

    with search_tab:
        genres = ["Svi"] + fetch_genres(driver)
        col1, col2 = st.columns(2)
        with col1:
            search_text = st.text_input("Pretraga po naslovu", key="movie_search_text")
            selected_genre = st.selectbox("Zanr", genres, key="movie_search_genre")
            min_year = st.number_input("Godina od", min_value=1900, max_value=2100, value=1970)
        with col2:
            avg_range = st.slider(
                "Opseg prosecne ocene",
                min_value=0.0,
                max_value=5.0,
                value=(0.0, 5.0),
                step=0.1,
            )
            max_year = st.number_input("Godina do", min_value=1900, max_value=2100, value=2030)

        rows = fetch_movie_catalog(
            driver,
            search_text=search_text,
            genre=selected_genre,
            min_year=int(min_year),
            max_year=int(max_year),
            min_avg_rating=float(avg_range[0]),
            max_avg_rating=float(avg_range[1]),
        )
        if rows:
            table_rows = [
                {
                    "Naslov": row["title"],
                    "Zanr": row.get("genre") or "-",
                    "Godina": row.get("year") or "-",
                    "Reditelj": row.get("director") or "-",
                    "Prosecna ocena": row["avg_rating"],
                    "Broj ocena": row["ratings_count"],
                }
                for row in rows
            ]
            st.dataframe(table_rows, width="stretch", hide_index=True)
        else:
            st.info("Nema filmova za izabrane filtere.")

    with create_tab:
        with st.form("create_movie_form", clear_on_submit=True):
            title = st.text_input("Naslov")
            genre = st.text_input("Zanr")
            year = st.number_input("Godina", min_value=1900, max_value=2100, value=2020)
            director = st.text_input("Reditelj")
            submitted = st.form_submit_button("Dodaj film")

        if submitted:
            created = create_movie(
                driver,
                title=title,
                genre=genre,
                year=int(year),
                director=director,
            )
            if created:
                st.success("Film je dodat.")
                st.rerun()
            else:
                st.warning("Dodavanje nije uspelo. Proveri polja i da li film vec postoji.")

    with update_tab:
        movie_rows = fetch_movie_catalog(driver)
        movie_titles = [row["title"] for row in movie_rows]
        if not movie_titles:
            st.info("Nema filmova za izmenu.")
        else:
            selected_movie = st.selectbox("Izaberi film", movie_titles, key="update_movie_selected")
            movie_data = next((row for row in movie_rows if row["title"] == selected_movie), None)
            if movie_data:
                with st.form("update_movie_form"):
                    new_title = st.text_input("Novi naslov", value=movie_data["title"])
                    new_genre = st.text_input("Zanr", value=movie_data.get("genre") or "")
                    new_year = st.number_input(
                        "Godina",
                        min_value=1900,
                        max_value=2100,
                        value=int(movie_data.get("year") or 2000),
                    )
                    new_director = st.text_input(
                        "Reditelj", value=movie_data.get("director") or ""
                    )
                    update_submitted = st.form_submit_button("Sacuvaj izmene")

                if update_submitted:
                    updated = update_movie(
                        driver,
                        original_title=selected_movie,
                        new_title=new_title,
                        genre=new_genre,
                        year=int(new_year),
                        director=new_director,
                    )
                    if updated:
                        st.success("Film je azuriran.")
                        st.rerun()
                    else:
                        st.warning("Azuriranje nije uspelo. Proveri da li naslov vec postoji.")

    with delete_tab:
        movie_titles = fetch_movies(driver)
        if not movie_titles:
            st.info("Nema filmova za brisanje.")
        else:
            selected_movie = st.selectbox("Film za brisanje", movie_titles, key="delete_movie_selected")
            confirm = st.checkbox("Potvrdjujem brisanje filma i svih njegovih ocena")
            if st.button("Obrisi film"):
                if not confirm:
                    st.warning("Potrebna je potvrda pre brisanja.")
                else:
                    deleted = delete_movie(driver, selected_movie)
                    if deleted:
                        st.success("Film je obrisan.")
                        st.rerun()
                    else:
                        st.error("Brisanje nije uspelo.")


def render_user_profile(driver, users):
    st.header("4) Korisnicki profil")

    if not users:
        st.info("Nema korisnika.")
        return

    profile_user = st.selectbox("Izaberi korisnika za profil", users, key="profile_user")
    summary = fetch_user_profile_summary(driver, profile_user)
    recent_rows = fetch_recent_ratings_for_user(driver, profile_user, limit=5)
    profile_recommendations = fetch_recommendations(driver, profile_user, threshold=4, limit=5)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Broj ocena", summary["ratings_count"])
    with col2:
        st.metric("Prosecna ocena", summary["avg_rating"])

    st.subheader("Omiljeni zanrovi")
    if summary["favorite_genres"]:
        st.dataframe(summary["favorite_genres"], width="stretch", hide_index=True)
    else:
        st.info("Nema dovoljno podataka za zanrove.")

    st.subheader("Poslednje i najjace ocene")
    if recent_rows:
        st.dataframe(
            [
                {
                    "Film": row["movie"],
                    "Zanr": row.get("genre") or "-",
                    "Godina": row.get("year") or "-",
                    "Ocena": row["rating"],
                }
                for row in recent_rows
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Korisnik jos nema ocena.")

    st.subheader("Preporuke")
    if profile_recommendations:
        st.dataframe(
            [
                {
                    "Film": row["movie"],
                    "Skor": row["score"],
                }
                for row in profile_recommendations
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Trenutno nema preporuka za izabranog korisnika.")


st.set_page_config(page_title="Movie Recommendation Engine", layout="wide")
st.title("Sistem za preporuku filmova")

uri, user, password = render_connection_sidebar()

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
render_user_creation(driver)

users = fetch_users(driver)

st.divider()
render_movie_management(driver)

movies = fetch_movies(driver)

st.divider()
render_rating_crud(driver, users, movies)

st.divider()
render_user_profile(driver, users)
