import streamlit as st

from db import get_connection
import pandas as pd
import altair as alt

try:
    conn = get_connection()
    st.success("Koneksi database berhasil!")
except Exception as e:
    st.error(f"Gagal konek ke database: {e}")


st.set_page_config(page_title="Music Streaming App", page_icon="📊", layout="wide")

st.title("Streamlit Music App")


user = st.session_state.get("selected_user", None)
if user:
    st.write(f"Selamat datang, **{user}**!")

@st.cache_data(ttl=60)  # cache 60 detik, bisa diubah sesuai kebutuhan
def get_summary_data():
    conn = get_connection()
    total_artists = pd.read_sql("SELECT COUNT(*) FROM artist;", conn).iloc[0, 0]
    total_songs = pd.read_sql("SELECT COUNT(*) FROM track;", conn).iloc[0, 0]

    latest_songs = pd.read_sql("""
        SELECT  title,a.album_title as album, ar.artist_name as artist FROM track t
JOIN album a ON a.album_id_spotify=t.spotify_id_album
JOIN artist ar ON ar.artist_id_spotify=a.artist_id_spotify
ORDER BY track_id desc
        LIMIT 5;
    """, conn)

    songs_per_artist = pd.read_sql("""
        SELECT  ar.artist_name as artist ,count(title) AS total_lagu FROM track t
JOIN album a ON a.album_id_spotify=t.spotify_id_album
JOIN artist ar ON ar.artist_id_spotify=a.artist_id_spotify
GROUP BY ar.artist_name
ORDER BY total_lagu DESC
LIMIT 10;
    """, conn)

    return total_artists, total_songs, latest_songs, songs_per_artist

# --- Ambil data ---
try:
    total_artists, total_songs, latest_songs, songs_per_artist = get_summary_data()
except Exception as e:
    st.error(f"Gagal ambil data: {e}")
    st.stop()

# --- Statistik utama ---
col1, col2 = st.columns(2)
col1.metric("Total Artis 🎤", total_artists)
col2.metric("Total Lagu 🎶", total_songs)

st.markdown("---")

# --- Lagu terbaru ---
st.subheader("🆕 Lagu Terbaru Ditambahkan")
if latest_songs.empty:
    st.info("Belum ada lagu yang ditambahkan.")
else:
    st.dataframe(latest_songs, use_container_width=True)

st.markdown("---")

# --- Grafik jumlah lagu per artis ---
st.subheader("📊 Jumlah Lagu per Artis (Top 10)")
if songs_per_artist.empty:
    st.info("Belum ada data lagu.")
else:
    chart = (
        alt.Chart(songs_per_artist)
        .mark_bar(color="#4B9CD3")
        .encode(
            x=alt.X("total_lagu:Q", title="Jumlah Lagu"),
            y=alt.Y("artist:N", sort="-x", title="Artis"),
            tooltip=["artist", "total_lagu"]
        )
        .properties(height=400)
    )
    st.altair_chart(chart, use_container_width=True)
