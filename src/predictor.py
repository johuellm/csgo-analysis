import json
import os
import pickle

import joblib
import torch
from gnn import GNN
from sklearn.preprocessing import OneHotEncoder
from torch.utils.data import Dataset
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.utils import add_self_loops


class GraphDatasetPredictor(Dataset):
    def __init__(
        self,
        graph_root_dir,
        area_encoder=None,
        label_to_id=None,
        node_type_encoder=None,
    ):
        super().__init__()
        self.graph_root_dir = graph_root_dir
        self.all_graphs = []
        self.area_ids = []

        # Search all folders for the graphs
        for root, _, files in os.walk(self.graph_root_dir):
            # print(f"Searching in {root} for .pkl files")
            for file in files:
                if file.endswith(".pkl"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "rb") as f:
                        graphs_in_file = pickle.load(f)
                        if isinstance(graphs_in_file, list):
                            for i, graph_data in enumerate(graphs_in_file):
                                self.all_graphs.append((graph_data, file_path, i))
                        else:
                            self.all_graphs.append((graphs_in_file, file_path, 0))

        # Collect data for normalizations
        self.node_type_ids = []
        self.area_ids = []
        self.all_utilities = []
        self.all_x = []
        self.all_y = []
        for graph_data, _, _ in self.all_graphs:
            for node in graph_data["nodes_data"].values():
                self.area_ids.append([node.get("areaId", 0)])
                self.node_type_ids.append([node.get("nodeType", 0)])
                self.all_utilities.append(node.get("totalUtility", 0))
                self.all_x.append(node.get("x", 0))
                self.all_y.append(node.get("y", 0))

        # AreaId OneHotEncoder
        if area_encoder is not None:
            self.area_encoder = area_encoder
        else:
            self.area_encoder = OneHotEncoder(
                sparse_output=False, handle_unknown="ignore"
            )
            self.area_encoder.fit(self.area_ids)

        # Node type normalization
        if node_type_encoder is not None:
            self.node_type_encoder = node_type_encoder
        else:
            self.node_type_encoder = OneHotEncoder(
                sparse_output=False, handle_unknown="ignore"
            )
            self.node_type_encoder.fit(self.node_type_ids)

        # Utility normalization
        self.min_utility = min(self.all_utilities)
        self.max_utility = max(self.all_utilities)
        self.utility_range = (
            self.max_utility - self.min_utility
            if self.max_utility != self.min_utility
            else 1
        )

        # Position normalization
        self.global_min_x, self.global_max_x = min(self.all_x), max(self.all_x)
        self.global_min_y, self.global_max_y = min(self.all_y), max(self.all_y)
        self.global_x_range = (
            self.global_max_x - self.global_min_x
            if self.global_max_x != self.global_min_x
            else 1
        )
        self.global_y_range = (
            self.global_max_y - self.global_min_y
            if self.global_max_y != self.global_min_y
            else 1
        )

        # Collect unique labels from all graphs
        if label_to_id is not None:
            self.label_to_id = label_to_id
        else:
            with open(
                "research_project\\tactic_labels\\de_dust2_tactics.json", "r"
            ) as f:
                tactics = json.load(f)
            strategies = [item["id"] for item in tactics]
            self.label_to_id = {label: idx for idx, label in enumerate(strategies)}

        # Convert each graph to a PyG Data object
        self.processed_graphs = [
            self._process_graph_data(graph_data, file_path, idx)
            for graph_data, file_path, idx in self.all_graphs
        ]

    def __len__(self):
        return len(self.processed_graphs)

    def __getitem__(self, idx):
        return self.processed_graphs[idx]

    def _process_graph_data(self, graph_dict, file_path, graph_idx):
        # selected_keys = ["x", "y", "hp", "armor", "isAlive", "hasBomb", "nodeType", "areaId"]
        # print("Nodes data keys:", graph_dict["nodes_data"].values())
        # print(graph_dict["graph_data"].keys(), graph_dict["graph_data"].values())

        # Extract graph features
        graph_data = graph_dict.get("graph_data", {})
        graph_features = [
            graph_data.get("seconds", 0) / 175.0,  # Normalize
        ]

        # Extract node features
        node_dicts = graph_dict["nodes_data"].values()
        node_features = []
        for node in node_dicts:
            # hp = node.get("hp", 0) / 100.0
            # armor = node.get("armor", 0) / 100.0
            norm_utility = (
                node.get("totalUtility", 0) - self.min_utility
            ) / self.utility_range

            norm_x = (node.get("x", 0) - self.global_min_x) / self.global_x_range
            norm_y = (node.get("y", 0) - self.global_min_y) / self.global_y_range

            area_onehot = self.area_encoder.transform([[node.get("areaId", 0)]])[0]

            binary_flags = [
                float(node.get("isAlive", 0)),
                float(node.get("hasBomb", 0)),
            ]

            node_type_onehot = self.node_type_encoder.transform(
                [[node.get("nodeType", 0)]]
            )[0]

            full_feature = (
                [norm_utility]
                + list(binary_flags)
                + list(area_onehot)
                + [norm_x, norm_y]
                + list(node_type_onehot)
            )

            node_features.append(full_feature)

        x = torch.tensor(node_features, dtype=torch.float)

        # Create node index mapping
        node_ids = sorted(graph_dict["nodes_data"].keys())
        node_map = {nid: i for i, nid in enumerate(node_ids)}
        num_nodes = len(node_map)

        # Validate and build edge index
        edge_list = []
        for src, dst, _ in graph_dict["edges_data"]:
            if src in node_map and dst in node_map:
                if node_map[src] < num_nodes and node_map[dst] < num_nodes:
                    edge_list.append([node_map[src], node_map[dst]])
                else:
                    print(
                        f"Warning: Invalid edge {src}->{dst} in graph {graph_idx} from {file_path}"
                    )

        if not edge_list:
            raise ValueError(f"No valid edges in graph {graph_idx} from {file_path}")

        edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()

        # Add self-loops with validation
        edge_index, _ = add_self_loops(edge_index, num_nodes=num_nodes)

        # Extract label
        strategy = graph_dict.get("graph_data", {}).get("strategy_used", "unknown")
        label = self.label_to_id.get(strategy, 0)

        return Data(
            x=x,
            edge_index=edge_index,
            y=torch.tensor(label, dtype=torch.long),
            graph_feat=torch.tensor(graph_features, dtype=torch.float),
        )


class Predictor:
    def __init__(self, model_path, dataset_path):
        self.model_path = model_path
        self.model_path = "research_project/models/checkpoint11.pt"
        self.dataset_path = dataset_path

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load unlabeled data
        print("Loading unlabeled data...")
        label_to_id = joblib.load("research_project/models/label_to_id.pkl")
        area_encoder = joblib.load("research_project/models/area_encoder.pkl")
        node_type_encoder = joblib.load("research_project/models/node_type_encoder.pkl")
        self.id_to_label = {v: k for k, v in label_to_id.items()}
        dataset = GraphDatasetPredictor(
            self.dataset_path,
            label_to_id=label_to_id,
            area_encoder=area_encoder,
            node_type_encoder=node_type_encoder,
        )
        self.loader = DataLoader(dataset)

        print(f"Dataset loaded with {len(dataset)} graphs.")
        checkpoint = torch.load(self.model_path)

        self.model = GNN(
            input_dim=checkpoint["input_dim"],
            hidden_channels=checkpoint["hidden_channels"],
            output_dim=checkpoint["output_dim"],
        )
        self.model.load_state_dict(checkpoint["model_state_dict"])

        optimizer = torch.optim.AdamW(self.model.parameters(), lr=0.0002)
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

        self.model.to(self.device)
        self.model.eval()
        print(f"Model loaded from {self.model_path}")

    def predict(self):
        predictions = []
        preds = []
        print("Predicting...")
        with torch.no_grad():
            for i, batch in enumerate(self.loader):
                batch = batch.to(self.device)
                out = self.model(batch)
                pred = out.argmax(dim=1)
                pred_labels = [self.id_to_label[p.item()] for p in pred]
                predictions.append(pred_labels)

        for i in predictions:
            preds.append(i[0])

        return preds
