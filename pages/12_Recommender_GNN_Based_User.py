import streamlit as st
import time
from recommender import build_graph, recommend_from_user, get_track_metadata,recommend_from_user_jaccard,recommend_from_user_gnn

st.title("🎧 Rekomendasi Musik Berdasarkan Graph User")

user = st.session_state.get("selected_user", None)
if user:
    st.write(f"Selamat datang, **{user}**!")
    user_id = user
else:
    st.warning("Masukkan User ID lewat page pengguna terlebih dahulu!")
    st.stop()

st.write(f"Rekomendasi GNN")

if not user_id:
    st.warning("Masukkan User ID terlebih dahulu.")
else:
    start = time.time()
    with st.spinner("Membangun graph & menghitung rekomendasi..."):
        #G2 = build_graph()
        recs2 = recommend_from_user_gnn(user_id)

    #st.write(recs2)
    if not recs2:
        st.error("Tidak ada rekomendasi untuk user ini.")
    else:
        track_ids2 = [t for t in recs2]
        df2 = get_track_metadata(track_ids2)
        
        #st.write(df2)
        # Masukkan score
        #score_map2 = dict(recs2)
        #df2['Score'] = df2['track_id'].map(score_map2)

        # Tambah tombol Spotify + Detail (sama seperti daftar musik)
        df2["Spotify"] = df2["spotify_track_link"].apply(
            lambda x: f'<a href="{x}" target="_blank">🎵</a>'
        )
        df2["Detail"] = df2["track_id"].apply(
            lambda x: f'<a href="/Detail_Music?spotify_id={x}&user_id={user}" target="_self">🔍 Detail</a>'
        )

        df2 = df2.drop(columns=["spotify_track_link","track_id"])
        
        #df2_sort = df2.sort_values(by='Score', ascending=False)

        st.markdown(df2.to_html(escape=False, index=False), unsafe_allow_html=True)
    end = time.time()
    elapsed = end - start
    st.write(f"Waktu GNN: {elapsed:.4f} detik")

st.write(f"Rekomendasi Graph Page Rank")
if not user_id:
    st.warning("Masukkan User ID terlebih dahulu.")
else:
    start = time.time()
    with st.spinner("Membangun graph & menghitung rekomendasi..."):
        G = build_graph()
        recs = recommend_from_user(user_id, G)

    if not recs:
        st.error("Tidak ada rekomendasi untuk user ini.")
    else:
        track_ids = [t[0] for t in recs]
        df = get_track_metadata(track_ids)

        # Masukkan score
        score_map = dict(recs)
        df['Score'] = df['track_id'].map(score_map)

        # Tambah tombol Spotify + Detail (sama seperti daftar musik)
        df["Spotify"] = df["spotify_track_link"].apply(
            lambda x: f'<a href="{x}" target="_blank">🎵</a>'
        )
        df["Detail"] = df["track_id"].apply(
            lambda x: f'<a href="/Detail_Music?spotify_id={x}&user_id={user}" target="_self">🔍 Detail</a>'
        )

        df = df.drop(columns=["spotify_track_link","track_id"])

        df_sort = df.sort_values(by='Score', ascending=False)
        
        st.markdown(df_sort.to_html(escape=False, index=False), unsafe_allow_html=True)
    end = time.time()
    elapsed = end - start
    st.write(f"Waktu Page Rank: {elapsed:.4f} detik")

st.write(f"Rekomendasi Graph Jaccard")

if not user_id:
    st.warning("Masukkan User ID terlebih dahulu.")
else:
    start = time.time()
    with st.spinner("Membangun graph & menghitung rekomendasi..."):
        G1 = build_graph()
        recs1 = recommend_from_user_jaccard(user_id, G1)

    if not recs1:
        st.error("Tidak ada rekomendasi untuk user ini.")
    else:
        track_ids1 = [t[0] for t in recs1]
        df1 = get_track_metadata(track_ids1)

        # Masukkan score
        score_map1 = dict(recs1)
        df1['Score'] = df1['track_id'].map(score_map1)

        # Tambah tombol Spotify + Detail (sama seperti daftar musik)
        df1["Spotify"] = df1["spotify_track_link"].apply(
            lambda x: f'<a href="{x}" target="_blank">🎵</a>'
        )
        df1["Detail"] = df1["track_id"].apply(
            lambda x: f'<a href="/Detail_Music?spotify_id={x}&user_id={user}" target="_self">🔍 Detail</a>'
        )

        df1 = df1.drop(columns=["spotify_track_link","track_id"])
        
        df1_sort = df1.sort_values(by='Score', ascending=False)

        st.markdown(df1_sort.to_html(escape=False, index=False), unsafe_allow_html=True)
    end = time.time()
    elapsed = end - start
    st.write(f"Waktu Jaccard: {elapsed:.4f} detik")

