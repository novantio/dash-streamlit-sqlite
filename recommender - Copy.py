import networkx as nx
import psycopg2
from db import get_connection
import math
import streamlit as st
import pickle

def build_graph():
    conn = get_connection()
    cur = conn.cursor()
    G = nx.Graph()

    # USER -> TRACK (Rating)
    cur.execute("SELECT r_user_id, r_spotify_id, r_rating FROM userreview")
    for user, track, rating in cur.fetchall():
        G.add_edge(f"user_{user}", f"track_{track}", weight=rating)

    # Track -> Album
    cur.execute("SELECT spotify_id_track, spotify_id_album FROM track")
    for track, album in cur.fetchall():
        G.add_edge(f"track_{track}", f"album_{album}", weight=1.5)

    # Album -> Artist
    cur.execute("SELECT album_id_spotify, artist_id_spotify FROM album")
    for album, artist in cur.fetchall():
        G.add_edge(f"album_{album}", f"artist_{artist}", weight=1)

    # Artist -> Genre
    cur.execute("SELECT artist_id_spotify, genre FROM artist_genres_view")
    for artist, genre in cur.fetchall():
        G.add_edge(f"artist_{artist}", f"genre_{genre.lower()}", weight=0.7)

    return G


def recommend_from_track(track_id, G, top_k=10):
    start_node = f"track_{track_id}"

    if start_node not in G:
        return []

    pr = nx.pagerank(
        G,
        alpha=0.85,
        personalization={start_node: 1},
        weight="weight"
    )

    recs = []
    for node, score in pr.items():
        if node.startswith("track_") and node != start_node:
            clean_id = node.replace("track_", "")
            recs.append((clean_id, score))

    recs.sort(key=lambda x: x[1], reverse=True)
    return recs[:top_k]
    
def recommend_from_track_jaccard(track_id, G, top_k=10):
    start_node = f"track_{track_id}"

    if start_node not in G:
        return []

    preds = nx.jaccard_coefficient(
        G,
        [(start_node, n) for n in G.nodes() if n != start_node]
    )

    recs = []
    for u, v, score in preds:
        other = v if u == start_node else u

        # Ubah NaN menjadi 0
        if math.isnan(score):
            score = 0

        if other.startswith("track_"):
            clean_id = other.replace("track_", "")
            recs.append((clean_id, score))

    recs.sort(key=lambda x: x[1], reverse=True)
    return recs[:top_k]

def recommend_from_user(user_id, G, top_k=10):
    start_node = f"user_{user_id}"

    if start_node not in G:
        return []

    pr = nx.pagerank(
        G,
        alpha=0.85,
        personalization={start_node: 1},
        weight="weight"
    )

    recs = []
    for node, score in pr.items():
        if node.startswith("track_"):
            track_id = node.replace("track_", "")
            recs.append((track_id, score))

    recs.sort(key=lambda x: x[1], reverse=True)
    return recs[:top_k]
    
def recommend_from_user_jaccard(user_id, G, top_k=10):
    start_node = f"user_{user_id}"

    if start_node not in G:
        return []

    # Hitung jaccard antara user ini dengan semua node lain
    preds = nx.jaccard_coefficient(
        G,
        [(start_node, n) for n in G.nodes() if n != start_node]
    )

    recs = []
    for u, v, score in preds:
        other = v if u == start_node else u

        # Perbaiki NaN -> 0
        if math.isnan(score):
            score = 0

        # Rekomendasikan hanya node bertipe track
        if other.startswith("track_"):
            track_id = other.replace("track_", "")
            recs.append((track_id, score))

    # Urutkan skor tertinggi
    recs.sort(key=lambda x: x[1], reverse=True)

    return recs[:top_k]

import pandas as pd

def get_track_metadata(track_ids):
    if not track_ids:
        return pd.DataFrame()

    conn = get_connection()
    placeholders = ','.join(['?'] * len(track_ids))

    query = f"""
    SELECT 
        t.spotify_id_track AS track_id,
        t.title AS Title,
        ar.artist_name AS Artis,
        a.album_title AS Album,
        t.spotify_track_link
    FROM track t
    JOIN album a ON a.album_id_spotify = t.spotify_id_album
    JOIN artist ar ON ar.artist_id_spotify = a.artist_id_spotify
    WHERE t.spotify_id_track IN ({placeholders})
    """

    df = pd.read_sql(query, conn, params=track_ids)
    return df

# ----------------------------
# Fungsi rekomendasi GNN
# ----------------------------
import torch
import torch.nn.functional as F
from torch_geometric.nn import HeteroConv, GraphConv

@st.cache_resource
def load_model_data():
    with open("hetero_data.pkl", "rb") as f:
        saved = pickle.load(f)
        data = saved["data"]
        idmap = saved["idmap"]

    class HeteroGNN(torch.nn.Module):
        def __init__(self, hidden_channels=64, out_channels=32):
            super().__init__()
            self.conv1 = HeteroConv({
                et: GraphConv(1, hidden_channels) for et in data.edge_types
            }, aggr='sum')
            self.conv2 = HeteroConv({
                et: GraphConv(hidden_channels, out_channels) for et in data.edge_types
            }, aggr='sum')

        def forward(self, x_dict, edge_index_dict):
            x_dict = self.conv1(x_dict, edge_index_dict)
            x_dict = {k: torch.relu(v) for k, v in x_dict.items()}
            x_dict = self.conv2(x_dict, edge_index_dict)
            return x_dict

    model = HeteroGNN()
    model.load_state_dict(torch.load("hetero_gnn.pt"))
    model.eval()

    return model, data, idmap

model, data, idmap = load_model_data()

def recommend_gnn(track_input):
    with torch.no_grad():
        out = model(data.x_dict, data.edge_index_dict)
        track_emb = F.normalize(out["track"], dim=1)

        # pastikan pakai prefix track_
        target_idx = idmap["track"].get(f"track_{track_input}", None)
        if target_idx is None:
            return []

        target_emb = track_emb[target_idx]
        sim = torch.matmul(track_emb, target_emb)
        topk = 11
        values, indices = torch.topk(sim, topk)

        similar_tracks = []
        for idx in indices:
            node_name = list(idmap["track"].keys())[list(idmap["track"].values()).index(idx.item())]
            if node_name != f"track_{track_input}":
                similar_tracks.append(node_name.replace("track_", ""))
            if len(similar_tracks) == 10:
                break

        return similar_tracks
        
def recommend_from_user_gnn(user_id, top_k=10):
    
    with torch.no_grad():
        out = model(data.x_dict, data.edge_index_dict)
        
        # embedding semua track dan user
        track_emb = F.normalize(out["track"], dim=1)
        user_emb = out["user"]

        # pastikan pakai prefix user_
        target_idx = idmap["user"].get(f"user_{user_id}", None)
        if target_idx is None:
            return []

        target_emb = user_emb[target_idx]

        # dot product user ↔ track
        sim = torch.matmul(track_emb, target_emb)

        # ambil top_k track
        values, indices = torch.topk(sim, top_k)

        recommended_tracks = []
        for idx in indices:
            node_name = list(idmap["track"].keys())[list(idmap["track"].values()).index(idx.item())]
            recommended_tracks.append(node_name.replace("track_", ""))

        return recommended_tracks
