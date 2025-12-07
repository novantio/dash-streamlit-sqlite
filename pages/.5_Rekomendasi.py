import streamlit as st
import pandas as pd
import altair as alt
from db import get_connection

import numpy as np
import pickle
from scipy.sparse import load_npz

# --- Load model & metadata ---
@st.cache_resource
def load_all():
    with open('model_knn.pkl', 'rb') as f:
        model_knn = pickle.load(f)
    with open('metadata.pkl', 'rb') as f:
        metadata = pickle.load(f)
    ratings = load_npz('ratings_matrix.npz')
    return model_knn, metadata, ratings

model_knn, metadata, ratings = load_all()

user_categories = metadata['user_categories']
product_categories = metadata['product_categories']

# --- Fungsi rekomendasi ---
def recommend_for_user(user_id, n_recommendations=5, k_neighbors=5):
    try:
        user_idx = list(user_categories).index(user_id)
    except ValueError:
        return ["❌ User tidak ditemukan di data"]

    distances, indices = model_knn.kneighbors(
        ratings[user_idx],
        n_neighbors=k_neighbors + 1
    )

    neighbors = indices.flatten()[1:]
    neighbor_ratings = ratings[neighbors].toarray()
    mean_ratings = np.mean(neighbor_ratings, axis=0)

    user_rated = ratings[user_idx].toarray().flatten() > 0
    mean_ratings[user_rated] = -1

    top_idx = np.argsort(-mean_ratings)[:n_recommendations]
    return product_categories[top_idx].tolist()

st.title("🎧 Sistem Rekomendasi Lagu (KNN)")

#user_id = st.text_input("Masukkan User ID:")
#n_recommendations = st.slider("Jumlah rekomendasi:", 1, 10, 5)

user = st.session_state.get("selected_user", None)
if user:
    st.write(f"Selamat datang, **{user}**!")
    user_id = user



if user:
    n_recommendations=10
    rekomendasi = recommend_for_user(user_id, n_recommendations)
    st.write(f"🎯 Rekomendasi untuk **{user_id}**:")
    
    stringrekomendasi = ",".join(f"'{x}'" for x in rekomendasi) 
    #st.write(f"rekomendasi: {stringrekomendasi }")

    conn = get_connection()
    st.set_page_config(page_title="Music Streaming App", page_icon="📊", layout="wide")

    artists_df = pd.read_sql("SELECT artist_id_spotify, artist_name FROM artist ORDER BY artist_name;", conn)
    artist_names = ["Semua Artis"] + artists_df["artist_name"].tolist()

    # --- Pilih artis ---
    #selected_artist = st.selectbox("Pilih Artis:", artist_names)

    # --- Input judul lagu ---
    #title_search = st.text_input("Cari judul lagu:")

    # --- Query dasar ---
    query = """
    SELECT title as Title, ar.artist_name Artis,a.album_title Album,spotify_track_link FROM track t
    JOIN album a ON a.album_id_spotify=t.spotify_id_album
    JOIN artist ar ON ar.artist_id_spotify=a.artist_id_spotify
    WHERE 1=1

    """
    params = []

    if stringrekomendasi != "":
        query += " AND spotify_id_track in ("+stringrekomendasi+")"
        #params.append(stringrekomendasi)

    query += " ORDER BY ar.artist_name, t.title limit 100;"

    #st.write(f"query: {query }")

    df = pd.read_sql(query, conn,params=params  )

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

else:
    st.warning("Masukkan User ID lewat page pengguna terlebih dahulu!")