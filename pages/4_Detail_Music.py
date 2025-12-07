import streamlit as st
import pandas as pd
from db import get_connection
from recommender import build_graph, recommend_from_track, get_track_metadata,recommend_from_track_jaccard,recommend_gnn
import time

st.set_page_config(page_title="Detail Lagu", page_icon="🎧", layout="wide")

st.title("🎵 Detail Lagu")

conn = get_connection()

# --- Pastikan user sudah login/terpilih
#user = st.session_state.get("selected_user", None)
#if not user:
#    st.warning("Silakan pilih atau login sebagai user terlebih dahulu.")
#    st.stop()

# --- Ambil parameter ID lagu dari URL (misal dari daftar lagu)
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

if user:
    st.write(f"Selamat datang, **{user}**!")

if not spotify_id[0]:
    st.warning("Tidak ada lagu yang dipilih. pilih lagu dari halaman daftar lagu.")
    st.stop()

# --- Ambil data lagu dari DB
song_query = """
SELECT t.title, ar.artist_name, a.album_title, t.spotify_track_link
FROM track t
JOIN album a ON a.album_id_spotify = t.spotify_id_album
JOIN artist ar ON ar.artist_id_spotify = a.artist_id_spotify
WHERE t.spotify_id_track = ?;
"""

#st.write(song_query)
song_df = pd.read_sql(song_query, conn, params=[spotify_id])

if song_df.empty:
    st.error("Lagu tidak ditemukan.")
    st.stop()

song = song_df.iloc[0]

# --- Tampilkan detail lagu
st.subheader(song["title"])
st.write(f"👤 **Artis:** {song['artist_name']}")
st.write(f"💿 **Album:** {song['album_title']}")
st.markdown(f"[🎧 Dengarkan di Spotify]({song['spotify_track_link']})")

st.markdown("---")

# --- Cek apakah user sudah pernah memberi rating
check_query = """
SELECT r_rating FROM userreview 
WHERE r_user_id = ? AND r_spotify_id = ?;
"""
check_df = pd.read_sql(check_query, conn, params=[user, spotify_id])

current_rating = check_df["r_rating"].iloc[0] if not check_df.empty else None

st.subheader("⭐ Beri Rating")

rating = st.slider("Nilai rating Anda (1–5):", 1, 5, current_rating or 3)

if st.button("💾 Simpan Rating"):
    with conn.cursor() as cur:
        if check_df.empty:
            # insert baru
            #cur.execute("""
            #    INSERT INTO userreview (r_user_id, r_spotify_id, r_rating)
            #    VALUES (?, ?, ?)
            #""", (user, spotify_id, rating))
            st.warning("Insert Disabled.")
        else:
            # update rating
            #cur.execute("""
            #    UPDATE userreview
            #    SET r_rating = ?
            #    WHERE r_user_id = ? AND r_spotify_id = ?
            #""", (rating, user, spotify_id))
            st.warning("Update Disabled.")
        #conn.commit()
    #st.success("✅ Rating berhasil disimpan!")
    


# ----------------------------
# Tampilkan rekomendasi GNN
# ----------------------------
st.subheader("🎶 Rekomendasi Lagu GNN")
start = time.time()
top_tracks_gnn = recommend_gnn(spotify_id)
if top_tracks_gnn:
    df_rec1 = get_track_metadata(top_tracks_gnn)
    df_rec1["Spotify"] = df_rec1["spotify_track_link"].apply(
        lambda x: f'<a href="{x}" target="_blank">🎵</a>'
    )
    df_rec1["Detail"] = df_rec1["track_id"].apply(
        lambda x: f'<a href="/Detail_Music?spotify_id={x}" target="_self">🔍 Detail</a>'
    )
    df_rec1 = df_rec1.drop(columns=["spotify_track_link","track_id"])
    st.markdown(df_rec1.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.warning("Tidak ada rekomendasi GNN untuk track ini.")
end = time.time()
elapsed = end - start
st.write(f"Waktu GNN: {elapsed:.4f} detik")

# ----------------------------
# Tampilkan rekomendasi Pagerank
# ----------------------------
st.subheader(f"🎶 Rekomendasi Graph Page Rank")
start = time.time()
track_id = spotify_id
if not track_id:
    st.warning("Masukkan Track ID terlebih dahulu.")
else:
    with st.spinner("Membangun graph & menghitung rekomendasi page rank..."):
        G = build_graph()
        recs = recommend_from_track(track_id, G)

    if not recs:
        st.error("Tidak ada rekomendasi untuk track ini.")
    else:
        top_track_ids = [t[0] for t in recs]
        df_rec = get_track_metadata(top_track_ids)

        # Gabungkan score ke dataframe
        scores_map = dict(recs)
        df_rec['Score'] = df_rec['track_id'].map(scores_map)

        # Tambah kolom Spotify / Detail
        df_rec["Spotify"] = df_rec["spotify_track_link"].apply(
            lambda x: f'<a href="{x}" target="_blank">🎵</a>'
        )
        df_rec["Detail"] = df_rec["track_id"].apply(
            lambda x: f'<a href="/Detail_Music?spotify_id={x}" target="_self">🔍 Detail</a>'
        )

        df_rec = df_rec.drop(columns=["spotify_track_link","track_id"])
        
        df_rec_sort = df_rec.sort_values(by='Score', ascending=False)

        st.markdown(df_rec_sort.to_html(escape=False, index=False), unsafe_allow_html=True)
end = time.time()
elapsed = end - start
st.write(f"Waktu Page Rank: {elapsed:.4f} detik")       

# ----------------------------
# Tampilkan rekomendasi Jaccard
# ----------------------------
st.subheader(f"🎶 Rekomendasi Graph Jaccard")       
start = time.time()        
if not track_id:
    st.warning("Masukkan Track ID terlebih dahulu.")
else:
    with st.spinner("Membangun graph & menghitung rekomendasi jaccard..."):
        G1 = build_graph()
        recs1 = recommend_from_track_jaccard(track_id, G1)

    if not recs1:
        st.error("Tidak ada rekomendasi untuk track ini.")
    else:
        top_track_ids1 = [t[0] for t in recs1]
        df_rec1 = get_track_metadata(top_track_ids1)

        # Gabungkan score ke dataframe
        scores_map1 = dict(recs1)
        df_rec1['Score'] = df_rec1['track_id'].map(scores_map1)

        # Tambah kolom Spotify / Detail
        df_rec1["Spotify"] = df_rec1["spotify_track_link"].apply(
            lambda x: f'<a href="{x}" target="_blank">🎵</a>'
        )
        df_rec1["Detail"] = df_rec1["track_id"].apply(
            lambda x: f'<a href="/Detail_Music?spotify_id={x}" target="_self">🔍 Detail</a>'
        )

        df_rec1 = df_rec1.drop(columns=["spotify_track_link","track_id"])
        
        df_rec1_sort = df_rec1.sort_values(by='Score', ascending=False)

        st.markdown(df_rec1_sort.to_html(escape=False, index=False), unsafe_allow_html=True)
end = time.time()
elapsed = end - start
st.write(f"Waktu Jaccard: {elapsed:.4f} detik")