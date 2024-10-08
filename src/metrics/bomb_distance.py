import matplotlib.pyplot as plt

from awpy.analytics.nav import area_distance, find_closest_area
from awpy.data import NAV
from awpy.visualization.plot import plot_map, position_transform
from matplotlib import patches

from models.data_manager import DataManager

## TODO: Find onlyy bombsite area tiles where you can plant
## TODO: Use distance lookup table to speed things up

def process_bomb_distance_frame(dm: DataManager, round_idx: int, frame_idx: int, plot_distance: bool = False):
  print("Calculating bomb distance metrics for round %d, frame %d" % (round_idx, frame_idx))
  map_name = dm.get_map_name()

  if map_name not in NAV:
    raise ValueError("Map not found.")

  # find shorted bombsite:
  closest_bombsite_dist = float("Inf")
  bombinfo = dm.get_bomb_info(round_idx, frame_idx)
  bomb_coords = [bombinfo[key] for key in bombinfo]
  area_bomb = find_closest_area(map_name, point=bomb_coords, flat=False)

  ## todo: find bombsite area with minimum distance from bomb
  for a in NAV[map_name]:
    area = NAV[map_name][a]
    if area["areaName"].startswith("Bombsite"):
      geodesic_dist = area_distance(map_name=map_name, area_a=a, area_b=area_bomb["areaId"], dist_type="geodesic")
      if geodesic_dist["distance"] < closest_bombsite_dist:
        closest_bombsite_dist = geodesic_dist["distance"]

  if not plot_distance:
    return closest_bombsite_dist

  fig, ax = plot_map(map_name=map_name, map_type='simpleradar', dark=True)

  for a in NAV[map_name]:
    area = NAV[map_name][a]
    southEastX = position_transform(map_name, area["southEastX"], "x")
    northWestX = position_transform(map_name, area["northWestX"], "x")
    southEastY = position_transform(map_name, area["southEastY"], "y")
    northWestY = position_transform(map_name, area["northWestY"], "y")
    width = (southEastX - northWestX)
    height = (northWestY - southEastY)

    color = "None"
    if a in geodesic_dist["areas"]:
      color = "red"

    rect = patches.Rectangle((northWestX, southEastY), width, height, linewidth=1, edgecolor="yellow",
                             facecolor=color)
    ax.add_patch(rect)

  fig.show()
  return closest_bombsite_dist



def process_bomb_distance_round(dm: DataManager, round_idx: int):
  print("Calculating bomb distance metrics for round %d" % round_idx)
  map_name = dm.get_map_name()

  if map_name not in NAV:
    raise ValueError("Map not found.")

  bomb_distance_metrics: list[float] = []
  for frame_idx, frame in enumerate(dm.get_game_round(round_idx)["frames"] or []) :
    frame_bomb_distance = process_bomb_distance_frame(dm, round_idx, frame_idx)
    bomb_distance_metrics.append(frame_bomb_distance)

  # plot  (for debug)
  import matplotlib.pyplot as plt
  import numpy as np
  plt.scatter(np.arange(len(bomb_distance_metrics)), bomb_distance_metrics)
  plt.show()

  return bomb_distance_metrics



def _util_find_bomb_area_ids(map_name: str):
  f, ax = plot_map(map_name=map_name, map_type='simpleradar', dark=True)

  f, ax = plt.subplots(1, figsize=[64.0,48.0], subplot_kw={"facecolor": "black"})
  ax.set_xlim(0, 6400)
  ax.set_ylim(0, 4800)

  for a in NAV[map_name]:
    area = NAV[map_name][a]
    southEastX = position_transform(map_name, area["southEastX"], "x")
    northWestX = position_transform(map_name, area["northWestX"], "x")
    southEastY = position_transform(map_name, area["southEastY"], "y")
    northWestY = position_transform(map_name, area["northWestY"], "y")
    width = (southEastX - northWestX)
    height = (northWestY - southEastY)
    col = "None"
    if area["areaName"].startswith("Bombsite"):
      col = "red"
    rect = patches.Rectangle((northWestX, southEastY), width, height, linewidth=1, edgecolor="yellow",
                             facecolor=col)
    ax.add_patch(rect)
    if area["areaName"].startswith("Bombsite"):
      ax.text(northWestX, northWestY, str(a), fontsize=4, color="white")
  f.show()


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

  process_bomb_distance_frame(dm, 5, 8, True)
