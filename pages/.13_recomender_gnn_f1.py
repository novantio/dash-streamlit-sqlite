import streamlit as st
import pandas as pd
import torch
import torch.nn.functional as F
from torch_geometric.nn import HeteroConv, GraphConv
import pickle

from db import get_connection
from recommender import build_graph, recommend_from_track, recommend_from_track_jaccard, get_track_metadata,recommend_gnn

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="Detail Lagu", page_icon="🎧", layout="wide")
st.title("🎵 Detail Lagu")

# ----------------------------
# Load model & data
# ----------------------------


# ----------------------------
# DB connection
# ----------------------------
conn = get_connection()

# ----------------------------
# Ambil parameter track dan user
# ----------------------------
query_params = st.query_params
spotify_id = query_params.get("spotify_id", [None])

user = st.session_state.get("selected_user", None)
if(user):
    user_id=user
else:
    user_id = query_params.get("user_id", [None])
    if(user_id[0]):
        st.session_state["selected_user"] = user_id
        user=user_id

st.write("sid",spotify_id)
st.write("uid",user)

if user:
    st.write(f"Selamat datang, **{user}**!")

if not spotify_id:
    st.warning("Tidak ada lagu yang dipilih. Pilih lagu dari halaman daftar lagu.")
    st.stop()

# ----------------------------
# Ambil data lagu
# ----------------------------
song_query = """
SELECT t.title, ar.artist_name, a.album_title, t.spotify_track_link
FROM track t
JOIN album a ON a.album_id_spotify = t.spotify_id_album
JOIN artist ar ON ar.artist_id_spotify = a.artist_id_spotify
WHERE t.spotify_id_track = %s;
"""
song_df = pd.read_sql(song_query, conn, params=[spotify_id])

if song_df.empty:
    st.error("Lagu tidak ditemukan.")
    st.stop()

song = song_df.iloc[0]

st.subheader(song["title"])
st.write(f"👤 **Artis:** {song['artist_name']}")
st.write(f"💿 **Album:** {song['album_title']}")
st.markdown(f"[🎧 Dengarkan di Spotify]({song['spotify_track_link']})")
st.markdown("---")




# ----------------------------
# Tampilkan rekomendasi GNN
# ----------------------------
st.subheader("🎶 Rekomendasi Lagu Berdasarkan GNN")
top_tracks_gnn = recommend_gnn(spotify_id)
if top_tracks_gnn:
    df_rec = get_track_metadata(top_tracks_gnn)
    st.dataframe(df_rec)
else:
    st.warning("Tidak ada rekomendasi GNN untuk track ini.")

# ----------------------------
# Rekomendasi Network / PageRank
# ----------------------------
st.subheader("🎶 Rekomendasi Lagu Berdasarkan Network PageRank")
with st.spinner("Membangun graph & menghitung rekomendasi PageRank..."):
    G = build_graph()
    recs = recommend_from_track(spotify_id, G)

if recs:
    top_track_ids = [t[0] for t in recs]
    df_rec = get_track_metadata(top_track_ids)
    scores_map = dict(recs)
    df_rec["Score"] = df_rec["track_id"].map(scores_map)
    st.dataframe(df_rec)
else:
    st.warning("Tidak ada rekomendasi PageRank untuk track ini.")

# ----------------------------
# Rekomendasi Network / Jaccard
# ----------------------------
st.subheader("🎶 Rekomendasi Lagu Berdasarkan Network Jaccard")
with st.spinner("Membangun graph & menghitung rekomendasi Jaccard..."):
    G_j = build_graph()
    recs_j = recommend_from_track_jaccard(spotify_id, G_j)

if recs_j:
    top_track_ids_j = [t[0] for t in recs_j]
    df_rec_j = get_track_metadata(top_track_ids_j)
    scores_map_j = dict(recs_j)
    df_rec_j["Score"] = df_rec_j["track_id"].map(scores_map_j)
    st.dataframe(df_rec_j)
else:
    st.warning("Tidak ada rekomendasi Jaccard untuk track ini.")
