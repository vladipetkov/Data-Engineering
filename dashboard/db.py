import sqlite3
import streamlit as st
from pathlib import Path

db_path = Path(__file__).parent /"spotify_database.db"

@st.cache_resource
def get_connection():
    return sqlite3.connect(db_path, check_same_thread=False)
