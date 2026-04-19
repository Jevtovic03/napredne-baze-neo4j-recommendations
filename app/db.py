from typing import Any, Dict, List, Optional

import streamlit as st
from neo4j import GraphDatabase


@st.cache_resource
def get_driver(uri: str, user: str, password: str):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
    except Exception:
        driver.close()
        raise
    return driver


def read_query(driver, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    params = params or {}
    with driver.session() as session:
        result = session.run(query, **params)
        return [record.data() for record in result]


def write_query(driver, query: str, params: Optional[Dict[str, Any]] = None) -> None:
    params = params or {}
    with driver.session() as session:
        session.run(query, **params).consume()
