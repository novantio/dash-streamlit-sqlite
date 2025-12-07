import streamlit as st
import pandas as pd
from db import get_connection

st.set_page_config(page_title="Music Streaming App", page_icon="📊", layout="wide")
st.title("📋 Daftar Review")

user = st.session_state.get("selected_user", None)
if user:
    st.write(f"Selamat datang, **{user}**!")
else:
    st.warning("Masukkan User ID lewat page pengguna terlebih dahulu!")
    st.stop()

conn = get_connection()
df = pd.read_sql("""select t.spotify_id_track AS track_id,
        t.title AS Title,
        ar.artist_name AS Artis,
        a.album_title AS Album,
        t.spotify_track_link
        from userreview ur 
JOIN track t on t.spotify_id_track = ur.r_spotify_id 
JOIN album a ON a.album_id_spotify = t.spotify_id_album
JOIN artist ar ON ar.artist_id_spotify = a.artist_id_spotify
where r_user_id='"""+user+"""';""", conn)

search = st.text_input("Cari lagu:")

# Tambah tombol Spotify + Detail (sama seperti daftar musik)
df["Spotify"] = df["spotify_track_link"].apply(
    lambda x: f'<a href="{x}" target="_blank">🎵</a>'
)
df["Detail"] = df["track_id"].apply(
    lambda x: f'<a href="/Detail_Music?spotify_id={x}&user_id={user}" target="_self">🔍 Detail</a>'
)

df = df.drop(columns=["spotify_track_link","track_id"])

if search:
    df = df[df["Title"].str.contains(search, case=False, na=False)]

#st.dataframe(df)
st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)