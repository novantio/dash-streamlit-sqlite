import streamlit as st
from recommender import build_graph, recommend_from_track, get_track_metadata

st.title("🎧 Rekomendasi Musik")

track_id = st.text_input("Masukkan Spotify Track ID yang ingin direkomendasikan:")

if st.button("Dapatkan Rekomendasi"):
    if not track_id:
        st.warning("Masukkan Track ID terlebih dahulu.")
    else:
        with st.spinner("Membangun graph & menghitung rekomendasi..."):
            G = build_graph()
            recs = recommend_from_track(track_id, G)

        if not recs:
            st.error("Tidak ada rekomendasi untuk track ini.")
        else:
            top_track_ids = [t[0] for t in recs]
            df = get_track_metadata(top_track_ids)

            # Gabungkan score ke dataframe
            scores_map = dict(recs)
            df['Score'] = df['track_id'].map(scores_map)

            # Tambah kolom Spotify / Detail
            df["Spotify"] = df["spotify_track_link"].apply(
                lambda x: f'<a href="{x}" target="_blank">🎵</a>'
            )
            df["Detail"] = df["track_id"].apply(
                lambda x: f'<a href="/Detail_Music?spotify_id={x}" target="_self">🔍 Detail</a>'
            )

            df = df.drop(columns=["spotify_track_link"])

            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
