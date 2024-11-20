import logging
import os
import pickle
from typing import Any

import networkx as nx

import stats
from awpy.analytics.nav import find_closest_area, area_distance
from awpy.data import NAV, AREA_DIST_MATRIX
from models.data_manager import DataManager

LOGGING_LEVEL = os.environ.get("LOGGING_INFO")
if LOGGING_LEVEL == "INFO":
  logging.basicConfig(level=logging.INFO)
elif LOGGING_LEVEL == "DEBUG":
  logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

KEYS_ROUND_LEVEL = ("tFreezeTimeEndEqVal", "tRoundStartEqVal", "tRoundSpendMoney", "tBuyType")
KEYS_FRAME_LEVEL = ("tick", "seconds", "bombPlanted")
KEYS_PLAYER_LEVEL = ("x", "y", "z", "velocityX", "velocityY", "velocityZ", "viewX", "viewY", "hp", "armor", "activeWeapon", "totalUtility", "isAlive", "isDefusing", "isPlanting", "isReloading", "isInBombZone", "isInBuyZone", "equipmentValue", "equipmentValueFreezetimeEnd", "equipmentValueRoundStart", "cash", "cashSpendThisRound", "cashSpendTotal", "hasHelmet", "hasDefuse", "hasBomb")
KEYS_BOMB_LEVEL = ("bombTick", "bombSeconds", "bombPlayerX", "bombPlayerY", "bombPlayerZ", "bombAction", "bombSite")

# DGL library requires int as node ids
# instead of randomly converting later, ensure that it is always 6,7,8, because
# players are 1-5
BOMB_NODE_INDEX = 6
BOMBSITE_A_NODE_INDEX = 7
BOMBSITE_B_NODE_INDEX = 8


def process_round(dm: DataManager, round_idx: int) -> list[list[Any]]:
  round = dm.get_game_round(round_idx)
  map_name = dm.get_map_name()

  # all variables on the round level --> graph data
  round_data = {key: round[key] for key in KEYS_ROUND_LEVEL}

  frames = dm._get_frames(round_idx)
  logger.info("Processing round %d with %d frames." % (round_idx, len(frames)))

  # store crucial bomb events for later analysis and estimating correct round ingame seconds.
  bomb_event_data = stats.process_bomb_data(round)

  # iterate and process each frame
  graphs = []
  error_frame_count = 0
  total_frames = len(frames)
  for frame_idx, frame in enumerate(frames):

    # check validity of frame
    valid_frame, err_text = stats.check_frame_validity(frame)
    if not valid_frame:
      logger.debug("Skipping frame %d entirely because %s." % (frame_idx, err_text))
      continue

    # all variables on the frame level are added to the graph level data.
    graph_data = {key: frame[key] for key in KEYS_FRAME_LEVEL} | round_data

    # include estimated seconds from bomb data for each frame
    if bomb_event_data["bombTick"] != None and frame["tick"] >= bomb_event_data["bombTick"]:
      graph_data["seconds"] = frame["seconds"] + bomb_event_data["bombSeconds"]
    else:
      graph_data["seconds"] = frame["seconds"]

    # all variables on the team and player level for the T side
    team = frame["t"]

    ### Create Node Data
    # iterate through all players, but keep them in same order every iteration
    nodes_data = {}
    edges_data = []
    for player_idx, player in enumerate(sorted(team["players"], key=lambda p: dm.get_player_idx_mapped(p["name"], "t", frame))):
      node_data = {key: player[key] for key in KEYS_PLAYER_LEVEL}
      node_data["areaId"] = find_closest_area(map_name, point=[node_data[key] for key in ("x", "y", "z")], flat=False)["areaId"]
      nodes_data[player_idx] = node_data

    # add bomb node
    #
    nodes_data[BOMB_NODE_INDEX] = dm.get_bomb_info(round_idx, frame_idx)
    nodes_data[BOMB_NODE_INDEX]["areaId"] = find_closest_area(map_name, point=[nodes_data["bomb"][key] for key in ("x", "y", "z")], flat=False)["areaId"]

    ### Create Edge Data
    # computes distances to bombsite
    try:
      distance_A, distance_B = distance_bombsites(dm, nodes_data)
    except ValueError as exc:
      logger.warning("Frame %d (%f%%): %s" % (frame_idx,frame_idx/total_frames, exc))
      error_frame_count += 1
      continue # skip errors
    for key in nodes_data.keys():
      edges_data.append((key, BOMBSITE_A_NODE_INDEX, {"dist":distance_A[key]}))
      edges_data.append((key, BOMBSITE_B_NODE_INDEX, {"dist":distance_B[key]}))

    # compute distances pairwise
    # CAUTION: distances from between 2 nodes can vary depending on direction (e.g., jump down, etc.).
    #          this implies a digraph for which networkx provides classes.
    #          As a result, we reverse the lists, so we start with bomb->player distance and end with player->bomb
    #          distances. This could be adjusted later.
    #          Update: currently switched to DiGraph and edges are double, one for each direction.
    for node_a in reversed(nodes_data.keys()):
      for node_b in reversed(nodes_data.keys()):
        # ignore self loops
        if node_a == node_b:
          continue
        edges_data.append((node_a, node_b, {"dist":_distance_internal(map_name, nodes_data[node_a]["areaId"], nodes_data[node_b]["areaId"])}))

    # add target site nodes after all distance calcuations, so we can always just take the entire dict as input
    nodes_data[BOMBSITE_A_NODE_INDEX] = None
    nodes_data[BOMBSITE_B_NODE_INDEX] = None

    # Creat graph from data
    graph = nx.DiGraph(**graph_data)
    graph.add_nodes_from(nodes_data)
    graph.add_edges_from(edges_data)
    graphs.append(graph)

  return graphs

def distance_bombsites(dm: DataManager, nodes: dict):
  #logger.debug("Calculating shortest distances for %d nodes." % len(nodes))
  map_name = dm.get_map_name()

  if map_name not in NAV:
    raise ValueError("Map not found.")

  # find shortest distances to both bombsites:
  closest_distances_A = {key: float("Inf") for key in nodes}
  closest_distances_B = {key: float("Inf") for key in nodes}

  ## Todo: find bombsite *plantable* area  with minimum distance from bomb
  for map_area_id in NAV[map_name]:
    map_area = NAV[map_name][map_area_id]
    if map_area["areaName"].startswith("BombsiteA"):
      for key, value in nodes.items():
        target_area = nodes[key]["areaId"]
        current_bombsite_dist = _distance_internal(map_name, map_area_id, target_area)
        # Set closest distance
        if current_bombsite_dist < closest_distances_A[key]:
          closest_distances_A[key] = current_bombsite_dist

    elif map_area["areaName"].startswith("BombsiteB"):
      for key, value in nodes.items():
        target_area = nodes[key]["areaId"]
        current_bombsite_dist = _distance_internal(map_name, map_area_id, target_area)
        # Set closest distance
        if current_bombsite_dist < closest_distances_B[key]:
          closest_distances_B[key] = current_bombsite_dist

  # sanity check
  for dist in list(closest_distances_A.values()) + list(closest_distances_B.values()):
    if dist == float("Inf"):
      raise ValueError("Could not find closest bombsite distances for at least one node.")

  # collate to tuple and return
  return closest_distances_A, closest_distances_B


def _distance_internal(map_name, area_a, area_b):
  # Use Area Distance Matrix if available, since it is faster
  # distance matrix uses strings as key
  area_a_str = str(area_a)
  area_b_str = str(area_b)
  if (map_name in AREA_DIST_MATRIX
      and area_a_str in AREA_DIST_MATRIX[map_name]
      and area_b_str in AREA_DIST_MATRIX[map_name][area_a_str]):
    current_bombsite_dist = AREA_DIST_MATRIX[map_name][area_a_str][area_b_str]["geodesic"]
  # Else: calculate distance from pairwise iteration over all areas in map
  else:
    if LOGGING_LEVEL == "DEBUG" and len(
        AREA_DIST_MATRIX) > 0:  # this happened once, not sure if debug overhead is needed
      logger.debug("Area matrix exists but does not contain areaid: %d" % area_a)
    geodesic_path = area_distance(map_name=map_name, area_a=area_a, area_b=area_b,
                                  dist_type="geodesic")
    current_bombsite_dist = geodesic_path["distance"]
  return current_bombsite_dist


def store_graphs_to_list_of_dicts(filename, *graphs):
  # from https://stackoverflow.com/questions/62615933/how-to-store-multiple-networkx-graphs-in-one-file
  list_of_dicts = [nx.to_dict_of_dicts(graph) for graph in graphs]
  with open(filename, 'wb') as f:
    pickle.dump(list_of_dicts, f)


def load_graphs_from_list_of_dicts(filename, create_using=nx.DiGraph):
  # from https://stackoverflow.com/questions/62615933/how-to-store-multiple-networkx-graphs-in-one-file
  with open(filename, 'rb') as f:
    list_of_dicts = pickle.load(f)
  return [create_using(graph) for graph in list_of_dicts]


def main():
  dm = DataManager(stats.EXAMPLE_DEMO_PATH, do_validate=False)
  output_filename_template = "graph-rounds-%d.pkl"
  logger.info("Processing match id: %s with %d rounds." % (dm.get_match_id(), dm.get_round_count()))

  graphs_total = 0
  for round_idx in range(dm.get_round_count()):
    output_filename = output_filename_template % round_idx
    logger.info("Converting round %d to file %s." % (round_idx, output_filename))

    # we need to swap mappings, because player sides switch here.
    # WARNING: This only works if teams player in MR15 setting.
    if round_idx == 15:
      dm.swap_player_mapping()

    # process round
    graphs = process_round(dm, round_idx)
    store_graphs_to_list_of_dicts(output_filename, *graphs)

    logger.info("%d graphs written to file." % len(graphs))
    graphs_total+= len(graphs)
  logger.info("SUCCESSFULLY COMPLETED: %d graphs written in total." % graphs_total)


if __name__ == '__main__':
  main()
