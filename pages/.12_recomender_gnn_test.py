import streamlit as st
import torch
import torch.nn.functional as F
from torch_geometric.nn import HeteroConv, GraphConv
import pickle

st.title("Track Recommendation")

track_input = st.text_input("Masukkan track_id (misal: track_1129292)")



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

with open("hetero_data.pkl", "rb") as f:
    saved = pickle.load(f)
    data = saved["data"]
    idmap = saved["idmap"]

if st.button("Cari top 10 mirip"):
    with torch.no_grad():
        model = HeteroGNN()  # harus sama class
        model.load_state_dict(torch.load(r"D:\me\s2 ugm\materi\2025-1\Information retrieval\tugas\dash-streamlit\hetero_gnn.pt"))
        model.eval()
        out = model(data.x_dict, data.edge_index_dict)
        track_emb = F.normalize(out["track"], dim=1)
        target_idx = idmap["track"].get(track_input, None)
        if target_idx is not None:
            target_emb = track_emb[target_idx]
            sim = torch.matmul(track_emb, target_emb)
            topk = 10 + 1
            values, indices = torch.topk(sim, topk)
            
            similar_tracks = []
            for idx in indices:
                node_name = list(idmap["track"].keys())[list(idmap["track"].values()).index(idx.item())]
                if node_name != track_input:
                    similar_tracks.append(node_name)
                if len(similar_tracks) == 10:
                    break
            st.write(similar_tracks)
        else:
            st.write("Track tidak ditemukan")
