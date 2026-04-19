import streamlit as st
from neo4j.exceptions import AuthError, ServiceUnavailable
from app.config import (
    DEFAULT_BOLT_URI,
    DEFAULT_PASSWORD,
    DEFAULT_USER,
    RECOMMENDATION_THRESHOLD_DEFAULT,
)
from app.db import get_driver
from app.seed import seed_data
from app.services.movies import fetch_movies
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
    st.header("2) Izmene")

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


def render_recommendations(driver, users):
    st.header("3) Neo4j preporuke")
    st.caption(
        "Ako je prag 4, racunaju se ocene 4 i 5. Ako je prag 3, ukljucuju se i trojke, "
        "pa preporuke postaju sire ali manje striktne."
    )

    if not users:
        st.info("Nema korisnika za preporuku.")
        return

    rec_user = st.selectbox("Izaberi korisnika", users, key="rec_user")
    threshold = st.slider(
        "Minimalna ocena koja ulazi u preporuke",
        min_value=3,
        max_value=5,
        value=RECOMMENDATION_THRESHOLD_DEFAULT,
    )
    rec_rows = fetch_recommendations(driver, rec_user, threshold)

    if rec_rows:
        table_rows = [
            {"Film": row["movie"], "Broj preporuka": row["score"]}
            for row in rec_rows
        ]
        st.dataframe(table_rows, width="stretch", hide_index=True)
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
render_rating_crud(driver, users, movies)

st.divider()
render_recommendations(driver, users)
