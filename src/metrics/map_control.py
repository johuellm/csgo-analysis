from collections import defaultdict, deque

import numpy as np
from awpy.analytics.map_control import calc_frame_map_control_values, _approximate_neighbors
from awpy.analytics.map_control import extract_teams_metadata
from awpy.analytics.nav import find_closest_area, calculate_tile_area
from awpy.data import NAV, NAV_GRAPHS
from awpy.types import BFSTileData, FrameMapControlValues
from awpy.visualization.plot import plot_map, _plot_map_control_from_dict

from models.data_manager import DataManager




def process_map_control_frame(dm: DataManager, round_idx: int, frame_idx: int, area_threshold: float, steps: int):
  """
  Args:
    area_threshold(float): maximum share of the map a single player can control (by area).
                           default is area_threshold = 1 / 20.
    steps(int): number of steps to use for BFS search in identifying neighboring area tiles.
                default is steps = 10
  """
  print("Calculating metrics for round %d" % round_idx)
  testframe = dm.get_frame(round_idx, frame_idx)
  map_name = dm.get_map_name()

  if map_name not in NAV:
    raise ValueError("Map not found.")

  # map list of 2-tuples to a lookup dicts for identifying neighboring tiles (for BFS) from NAV map graph
  tile_to_neighbors: dict[int, set[int]] = defaultdict(set)
  for tile_1, tile_2 in list(NAV_GRAPHS[map_name].edges):
    tile_to_neighbors[tile_1].add(tile_2)
    tile_to_neighbors[tile_2].add(tile_1)

  # get alive player locations from frame
  coords = ("x", "y", "z")
  alive_players_locations_t: list[list[float]] = [
    [player[dim] for dim in coords]
    for player in testframe["t"]["players"] or []
    if player["isAlive"]
  ]
  alive_players_locations_ct: list[list[float]] = [
    [player[dim] for dim in coords]
    for player in testframe["ct"]["players"] or []
    if player["isAlive"]
  ]

  # use euclidian distance to find occupied tile for each player from player location
  t_tiles = [
    find_closest_area(map_name, i)["areaId"]
    for i in alive_players_locations_t
  ]
  ct_tiles = [
    find_closest_area(map_name, i)["areaId"]
    for i in alive_players_locations_ct
  ]

  # use breadh-first-search to identify map control
  t_control_values = _bfs(map_name, t_tiles, tile_to_neighbors, area_threshold, steps)
  ct_control_values = _bfs(map_name, ct_tiles, tile_to_neighbors, area_threshold, steps)

  # plot results (for debug)
  figure, axes = plot_map(map_name=map_name, map_type="simpleradar", dark=True)
  _plot_map_control_from_dict(
    map_name,
    FrameMapControlValues(t_control_values, ct_control_values),
    axes,
    extract_teams_metadata(testframe)
  )
  figure.show()



# generates various metrics depending on configuration, 1 value per frame
def process_map_control_round(dm: DataManager, round_idx: int, frame_idx: int):
  print("Calculating metrics for round %d" % round_idx)
  testframe = dm.get_frame(round_idx, frame_idx)
  map_name = dm.get_map_name()

  if map_name not in NAV:
    raise ValueError("Map not found.")

  map_control_metrics: list[float] = []
  for frame in dm.get_game_round(round_idx)["frames"] or []:
    map_control_values = calc_frame_map_control_values(map_name, frame)
    current_frame_metric = _calc_map_control_metric_from_dict(
      map_name,
      map_control_values,
      True,
      0,
      False)
    map_control_metrics.append(current_frame_metric)

  # plot  (for debug)
  # import matplotlib.pyplot as plt
  # plt.scatter(np.arange(len(map_control_metrics)), map_control_metrics)
  # plt.show()

  return map_control_metrics



def _calc_map_control_metric_from_dict(
      map_name: str,
      mc_values: FrameMapControlValues,
      occupied_only: bool = True,
      norm: int = 0,
      absolute: bool = False
  ) -> float:
    """Return map control metric given FrameMapControlValues object.

    Map Control metric is used to quantify how much of the map is controlled
    by T/CT. Each tile is given a value between -1 (complete T control) and 1
    (complete CT control). If a tile is controlled by both teams, a value is
    found by taking the ratio between the sum of T values and sum of T and
    CT values. Once all of the tiles' values are calculated, a weighted sum
    is done on the tiles' values where the tiles' area is the weights.
    This weighted sum is transformed to fit the range [-1, 1] and then
    returned as the map control metric.

    Args:
        map_name (str): Map used in calculate_tile_area
        mc_values (FrameMapControlValues): Object containing map control
            values for both teams.
            Expected format that of calc_frame_map_control_values output

    Returns: Map Control Metric
    """

    if not occupied_only and not absolute:
      raise ValueError("All tiles and relative do not work together. Use norm instead.")


    current_map_control_value: list[float] = []
    tile_areas: list[float] = []
    if occupied_only:
      all_tiles = set(mc_values.ct_values) | set(mc_values.t_values)
    else:
      all_tiles = NAV[map_name].keys()

    for tile in all_tiles:
      ct_val, t_val = mc_values.ct_values[tile], mc_values.t_values[tile]

      # map control values are between 0 and 1, depending how much T side controls
      if absolute:
        current_map_control_value.append(sum(t_val))
      else:
        current_map_control_value.append(sum(t_val) / (sum(ct_val) + sum(t_val)))
      tile_areas.append(calculate_tile_area(map_name, int(tile)))

    np_current_map_control_value = np.array(current_map_control_value)
    np_tile_areas = np.array(tile_areas)

    # Normalize from -1 to 1 for ct possession weighted by tile area (ONLY occupied tiles)
    if norm == 0:
      return (
          (sum(np_current_map_control_value * np_tile_areas) / sum(np_tile_areas)) * 2
      ) - 1

    # Normalize from 0 to 1 for ct possession, weighted by tile area (ONLY occupied tiles)
    elif norm == 1:
      return (
          (sum(np_current_map_control_value * np_tile_areas) / sum(np_tile_areas))
      )

    # No normalization, weighted by tile area (ONLY occupied tiles)
    elif norm == 2:
      return (
          (sum(np_current_map_control_value * np_tile_areas))
      )

    else:
      raise ValueError("Invalid norm parameter value. Was %d and should be 0, 1, or 2" % norm)



def _bfs(map_name: str,
         current_tiles: list[int],
         neighbor_info: dict[int, set[int]],
         area_threshold: float = 1 / 20,
         steps: int = 10):
  """Helper function to run bfs from given tiles to generate map_control values dict.

  Values are allocated to tiles depending on how many tiles are between it
  and the source tile (aka tile distance). The smaller the tile distance,
  the close the tile's value is to 1. Tiles are considered until the cumulative
  tile area reaches the current map's navigable area * area_threshold, which is
  1/20 as a default. This means the BFS search will stop once the cumulative tile
  area reaches this threshold.

  Notes:
    - cannot get more than 20% of map per player
    - in theory, with 5 players, exactly 100% would be possible
    - each area in BFS lowers control value by 0.1 (i.e., focal area = 1.0, first neighbor = 0.9, next neighbor = 0.8, etc.)
      determined by step_denominator

  Args:
      map_name (str): Map for current_tiles
      current_tiles (TileId): List of source tiles for bfs iteration(s)
      neighbor_info (dict): Dictionary mapping tile to its navigable neighbors
      area_threshold (float): Percentage representing amount of map's total
                              navigable area which is the max cumulative tile
                              area for each bfs algorithm

  Returns:
      dict[int, list[float]] containing map control values

  Raises:
      ValueError: If area_threshold <= 0
  """
  if area_threshold <= 0:
    msg = "Invalid area_threshold value. Must be > 0."
    raise ValueError(msg)

  total_map_area = 0
  for tile in NAV[map_name]:
    total_map_area += calculate_tile_area(map_name, tile)

  map_control_values: dict[int, list[float]] = defaultdict(list)
  for cur_start_tile in current_tiles:
    tiles_seen: set[int] = set()

    # start tile gets value control value of 1.0
    # go 10 steps deep in BFS
    # each step gets -0.1 less control value
    start_tile = BFSTileData(
      tile_id=cur_start_tile, map_control_value=1.0, steps_left=steps
    )

    queue: deque[BFSTileData] = deque([start_tile])

    current_player_area = 0

    while queue and current_player_area < total_map_area * area_threshold:
      cur_tile = queue.popleft()
      cur_id = cur_tile.tile_id
      if cur_id not in tiles_seen:
        tiles_seen.add(cur_id)
        map_control_values[cur_id].append(cur_tile.map_control_value)

        neighbors = list(neighbor_info[cur_id])
        if len(neighbors) == 0:
          neighbors = [
            tile.tile_id
            for tile in _approximate_neighbors(map_name, cur_id)   # retrieves neighbors by identifying 5 areas with minimal distance to focal area
          ]

        queue.extend(
          [
            BFSTileData(
              tile_id=neighbor,
              map_control_value=max((cur_tile.steps_left - 1) / steps, 0.1),
              steps_left=cur_tile.steps_left - 1,
            )
            for neighbor in neighbors
          ]
        )

        cur_tile_area = calculate_tile_area(map_name, cur_id)
        current_player_area += cur_tile_area

  return map_control_values


if __name__ == "__main__":
  from pathlib import Path
  import os
  demo_path = os.path.join(os.getcwd(), 'demos/esta/lan/de_dust2/00e7fec9-cee0-430f-80f4-6b50443ceacd.json')
  # demo_path = Path(__file__).parent / '../demos/esta/lan/de_dust2/00e7fec9-cee0-430f-80f4-6b50443ceacd.json'
  # demo_path = Path(__file__).parent / '../../demos/esta/lan/de_dust2/00e7fec9-cee0-430f-80f4-6b50443ceacd.json'
  dm = DataManager(demo_path, do_validate=False)
  # testframe = dm.get_frame(5, 8)
  # map_control_fig, map_control_axes = plot_frame_map_control(dm.get_map_name(), testframe, plot_type='players')
  # map_control_fig.show()

  process_map_control_frame(dm, 5, 8, 1 / 10, 10)
  process_map_control_round(dm, 5, 8)
