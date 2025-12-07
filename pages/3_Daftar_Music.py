import streamlit as st
import pandas as pd
from db import get_connection

st.title("📋 Daftar Track")

user = st.session_state.get("selected_user", None)
if user:
    st.write(f"Selamat datang, **{user}**!")

conn = get_connection()
st.set_page_config(page_title="Music Streaming App", page_icon="📊", layout="wide")

artists_df = pd.read_sql("SELECT artist_id_spotify, artist_name FROM artist ORDER BY artist_name;", conn)
artist_names = ["Semua Artis"] + artists_df["artist_name"].tolist()

# --- Pilih artis ---
selected_artist = st.selectbox("Pilih Artis:", artist_names)

# --- Input judul lagu ---
title_search = st.text_input("Cari judul lagu:")

# --- Query dasar ---
query = """
SELECT title as Title, ar.artist_name Artis,a.album_title Album,spotify_track_link FROM track t
JOIN album a ON a.album_id_spotify=t.spotify_id_album
JOIN artist ar ON ar.artist_id_spotify=a.artist_id_spotify
WHERE 1=1

"""
params = []

# Filter berdasarkan artis
if selected_artist != "Semua Artis":
    query += " AND ar.artist_name= %s"
    params.append(selected_artist)

# Filter berdasarkan judul
if title_search:
    query += " AND t.title ILIKE %s"
    params.append(f"%{title_search}%")

query += " ORDER BY ar.artist_name, t.title limit 100;"

df = pd.read_sql(query, conn,params=params)

# --- Tampilkan hasil ---
#if df.empty:
#    st.warning("😅 Tidak ada lagu yang cocok.")
#else:
#    st.dataframe(df, use_container_width=True)


if not df.empty:
    df["Spotify"] = df["spotify_track_link"].apply(
        lambda x: f'<a href="{x}" target="_blank">🎵</a>'
    )
    df["Detail"] = df["spotify_track_link"].apply(
        lambda x: f'<a href="/Detail_Music?spotify_id={x.split("/")[-1]}&user_id={user}" target="_self">🔍 Detail</a>'
    )

    df_display = df.drop(columns=["spotify_track_link"])  # sembunyikan kolom link asli
    st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.warning("😅 Tidak ada lagu yang cocok.")