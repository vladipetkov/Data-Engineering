import sqlite3
import streamlit as st

@st.cache_resource
def get_connection():
    return sqlite3.connect("spotify_database.db", check_same_thread=False)

conn = get_connection()
cursor = conn.cursor()

