import streamlit as st
import pandas as pd
from db import get_connection

st.set_page_config(page_title="Music Streaming App", page_icon="📊", layout="wide")
st.title("📋 Daftar Genre")

user = st.session_state.get("selected_user", None)
if user:
    st.write(f"Selamat datang, **{user}**!")
else:
    st.warning("Masukkan User ID lewat page pengguna terlebih dahulu!")
    st.stop()
    
conn = get_connection()
sqlQuery ="""
SELECT  t.title, max(g.genre) genre, t.spotify_track_link
FROM track t
JOIN album a ON t.spotify_id_album = a.album_id_spotify
JOIN artist art ON a.artist_id_spotify = art.artist_id_spotify
JOIN artist_genres_view g ON art.artist_id_spotify = g.artist_id_spotify
WHERE g.genre IN (
SELECT gen.genre FROM userreview r
JOIN track t ON t.spotify_id_track=r.r_spotify_id
JOIN album a ON a.album_id_spotify = t.spotify_id_album
JOIN artist ar ON ar.artist_id_spotify=a.artist_id_spotify
JOIN artist_genres_view gen ON gen.artist_id_spotify=ar.artist_id_spotify
WHERE r.r_rating>=4 AND r.r_user_id='"""+user+"""'
GROUP BY gen.genre,r.r_user_id
ORDER BY COUNT(*) DESC
LIMIT 3
)
AND t.spotify_id_track NOT IN (
    SELECT r_spotify_id FROM userreview WHERE r_user_id = '"""+user+"""'
)
GROUP BY t.spotify_id_track,  t.title, t.spotify_track_link
LIMIT 20;"""
df = pd.read_sql(sqlQuery, conn)

#search = st.text_input("Cari artis:")
#if search:
#    df = df[df["artist_name"].str.contains(search, case=False, na=False)]

if not df.empty:
    df["Spotify"] = df["spotify_track_link"].apply(
        lambda x: f'<a href="{x}" target="_blank">🎵</a>'
    )
    
    df["Detail"] = df["spotify_track_link"].apply(
            lambda x: f'<a href="/Detail_Music?spotify_id={x.split("/")[-1]}&user_id={user}" target="_self">🔍 Detail</a>'
    )
    df_display = df.drop(columns=["spotify_track_link"])  # sembunyikan kolom link asli
    st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

#st.dataframe(df)