import streamlit as st
import pandas as pd
import altair as alt
from db import get_connection

st.set_page_config(page_title="Music Streaming App", page_icon="📊", layout="wide")
st.title("🎧 Music Dashboard")

# --- Koneksi database cached ---
conn = get_connection()
#st.success("Koneksi database berhasil!")

# --- Fungsi cached untuk ambil data ---
@st.cache_data(ttl=60)
def get_summary_data():
    conn = get_connection()  # buat koneksi di dalam fungsi cache
    # total artis & total lagu
    total_artists = pd.read_sql("SELECT COUNT(*) FROM artist;", conn).iloc[0, 0]
    total_songs = pd.read_sql("SELECT COUNT(*) FROM track;", conn).iloc[0, 0]

    # 5 lagu terbaru
    latest_songs = pd.read_sql("""
        SELECT title,a.album_title, ar.artist_name,a.release_date FROM track t
JOIN album a ON a.album_id_spotify=t.spotify_id_album
JOIN artist ar ON ar.artist_id_spotify=a.artist_id_spotify
ORDER BY a.release_date DESC
LIMIT 5;
    """, conn)

    # jumlah lagu per artis (top 10)
    songs_per_artist = pd.read_sql("""
        SELECT album_title title,release_date date,ar.artist_name artis,a.total_tracks total_lagu FROM album a
JOIN artist ar ON ar.artist_id_spotify=a.artist_id_spotify

ORDER BY a.release_date desc

LIMIT 10;
    """, conn)

    # lagu per tahun rilis
    songs_per_year = pd.read_sql("""
        SELECT 
    strftime('%Y', a.release_date) AS years,
    COUNT(t.title) AS total_lagu
FROM track t
JOIN album a ON a.album_id_spotify = t.spotify_id_album
JOIN artist ar ON ar.artist_id_spotify = a.artist_id_spotify
GROUP BY strftime('%Y', a.release_date)
ORDER BY strftime('%Y', a.release_date) DESC;
    """, conn)

    # genre paling populer (top 10)
    genre_popular = pd.read_sql("""
         SELECT artist.artist_name artis, artist.artist_followers follower FROM artist
 ORDER BY artist_followers desc
 LIMIT 5;
    """, conn)

    return total_artists, total_songs, latest_songs, songs_per_artist, songs_per_year, genre_popular

# --- Ambil data cached ---
try:
    total_artists, total_songs, latest_songs, songs_per_artist, songs_per_year, genre_popular = get_summary_data()
except Exception as e:
    st.error(f"Gagal ambil data: {e}")
    st.stop()

# --- Statistik utama ---
col1, col2 = st.columns(2)
col1.metric("Total Artis 🎤", total_artists)
col2.metric("Total Lagu 🎶", total_songs)

st.markdown("---")

# --- Lagu terbaru ---
st.subheader("🆕 Lagu Terakhir Release")
if latest_songs.empty:
    st.info("Belum ada lagu yang ditambahkan.")
else:
    st.dataframe(latest_songs, use_container_width=True)

st.markdown("---")

# --- Grafik jumlah lagu per artis ---
st.subheader("📊 Jumlah Lagu per Album (latest)")
if songs_per_artist.empty:
    st.info("Belum ada data lagu.")
else:
    chart1 = (
        alt.Chart(songs_per_artist)
        .mark_bar(color="#4B9CD3")
        .encode(
            x=alt.X("total_lagu:Q", title="Jumlah Lagu"),
            y=alt.Y("title:N", sort="-x", title="Artis"),
            tooltip=["title", "total_lagu"]
        )
        .properties(height=400)
    )
    st.altair_chart(chart1, use_container_width=True)

st.markdown("---")

# --- Grafik lagu per tahun rilis ---
st.subheader("📈 Lagu per Tahun Rilis")
if songs_per_year.empty:
    st.info("Belum ada data tahun rilis.")
else:
    chart2 = (
        alt.Chart(songs_per_year)
        .mark_line(point=True, color="#FF6F61")
        .encode(
            x=alt.X("years:O", title="Tahun Rilis"),
            y=alt.Y("total_lagu:Q", title="Jumlah Lagu"),
            tooltip=["years", "total_lagu"]
        )
        .properties(height=400)
    )
    st.altair_chart(chart2, use_container_width=True)

st.markdown("---")

# --- Grafik genre paling populer ---
st.subheader("🎼 Artis Paling Populer (Top 5)")
if genre_popular.empty:
    st.info("Belum ada data genre.")
else:
    chart3 = (
        alt.Chart(genre_popular)
        .mark_bar(color="#FFA500")
        .encode(
            x=alt.X("follower:Q", title="Jumlah follower"),
            y=alt.Y("artis:N", sort="-x", title="Artis"),
            tooltip=["artis", "follower"]
        )
        .properties(height=400)
    )
    st.altair_chart(chart3, use_container_width=True)
