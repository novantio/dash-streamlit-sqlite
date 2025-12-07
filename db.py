import sqlite3
import streamlit as st

@st.cache_resource
def get_connection():
    """Bikin koneksi SQLite dan simpan di cache Streamlit"""
    conn = sqlite3.connect("dbmusic.sqlite", check_same_thread=False)
    conn.row_factory = sqlite3.Row  # supaya hasil bisa diakses seperti dict
    
    return conn
