import csv
import os
import pickle
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def parse_graph_data(graph_data):
  return list(graph_data.values())


def parse_node_data(node_data):
  # bug in create_graphs.py: players are ids 0,1,2,3,4 but bomb and bombsites are 6,7,8
  lines = []
  for k, v in node_data.items():
    lines.extend([k] + list(v.values()))
  return lines


def parse_edges_data(edges_data):
  lines = []
  for edge in edges_data:
    lines.extend([edge[0], edge[1], edge[2]['dist']])
  return lines


def main():
  graphs_folder = Path(os.environ.get("GRAPHS_OUTPUT_DIR"))
  try:
    with open("output.csv", "w", newline="", encoding="utf-8") as f_out:
      writer = csv.writer(f_out)
      for pkl_file in graphs_folder.rglob("*.pkl"):
        demo_name = pkl_file.parent.name
        round_idx = pkl_file.stem.rpartition("-")[2]
        with open(pkl_file, "rb") as f:
          frames = pickle.load(f)
          for frame in frames:
            writer.writerow(
              [demo_name, round_idx] +
              parse_graph_data(frame["graph_data"]) +
              parse_node_data(frame["nodes_data"]) +
              parse_edges_data(frame["edges_data"]))
      return
  except Exception as e:
    print(f"Failed: {e}")


if __name__ == "__main__":
  main()
