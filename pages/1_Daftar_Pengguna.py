import streamlit as st
import pandas as pd
from db import get_connection

st.set_page_config(page_title="Music Streaming App", page_icon="📊", layout="wide")
st.title("📋 Daftar Pengguna")

user = st.session_state.get("selected_user", None)
if user:
    st.write(f"Selamat datang, **{user}**!")

# --- Ambil data pengguna dari DB
conn = get_connection()
df = pd.read_sql("SELECT user_name FROM pengguna limit 20;", conn)

# --- Fitur pencarian
search = st.text_input("Cari Pengguna:")
if search:
    df = pd.read_sql("SELECT user_name FROM pengguna where upper(user_name) like upper('%"+search+"%') limit 20;", conn)
else:
    df = pd.read_sql("SELECT user_name FROM pengguna limit 20;", conn)

# --- Tampilkan daftar pengguna dengan tombol "Pilih"
for i, row in df.iterrows():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(row["user_name"])
    with col2:
        if st.button("Set Session", key=f"set_{i}"):
            st.session_state["selected_user"] = row["user_name"]
            st.success(f"✅ Session diset ke: {row['user_name']}")
            st.rerun()  # refresh supaya efek langsung terlihat

# --- Tampilkan session yang aktif
if "selected_user" in st.session_state:
    st.info(f"👤 Pengguna aktif: {st.session_state['selected_user']}")
