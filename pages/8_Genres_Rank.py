import streamlit as st
import pandas as pd
from db import get_connection

st.set_page_config(page_title="Music Streaming App", page_icon="📊", layout="wide")
st.title("📋 Daftar Artis")

user = st.session_state.get("selected_user", None)
if user:
    st.write(f"Selamat datang, **{user}**!")
else:
    st.warning("Masukkan User ID lewat page pengguna terlebih dahulu!")
    st.stop()
    
conn = get_connection()
sqlQuery ="""SELECT gen.genre,COUNT(*) FROM userreview r
JOIN track t ON t.spotify_id_track=r.r_spotify_id
JOIN album a ON a.album_id_spotify = t.spotify_id_album
JOIN artist ar ON ar.artist_id_spotify=a.artist_id_spotify
JOIN artist_genres_view gen ON gen.artist_id_spotify=ar.artist_id_spotify
WHERE r.r_rating>=4 AND r.r_user_id='"""+user+"""'
GROUP BY gen.genre,r.r_user_id
ORDER BY COUNT(*) DESC;"""
df = pd.read_sql(sqlQuery, conn)

#search = st.text_input("Cari artis:")
#if search:
#    df = df[df["artist_name"].str.contains(search, case=False, na=False)]

st.dataframe(df)