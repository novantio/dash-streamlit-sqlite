import streamlit as st
import pandas as pd
from db import get_connection

st.set_page_config(page_title="Music Streaming App", page_icon="📊", layout="wide")
st.title("📋 Daftar Artis")

user = st.session_state.get("selected_user", None)
if user:
    st.write(f"Selamat datang, **{user}**!")

conn = get_connection()
df = pd.read_sql("SELECT artist_name,artist_country,artist_followers,artist_genres FROM artist;", conn)

search = st.text_input("Cari artis:")
if search:
    df = df[df["artist_name"].str.contains(search, case=False, na=False)]

st.dataframe(df)