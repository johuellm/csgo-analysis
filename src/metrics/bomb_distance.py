import matplotlib.pyplot as plt

from awpy.analytics.nav import area_distance
from awpy.data import NAV
from awpy.visualization.plot import plot_map, position_transform
from matplotlib import patches

from models.data_manager import DataManager


def process_bomb_distance(dm: DataManager, round_idx: int, frame_idx: int, plot: bool = False):
  print("Calculating metrics for round %d" % round_idx)
  testframe = dm.get_frame(round_idx, frame_idx)
  map_name = dm.get_map_name()

  if map_name not in NAV:
    raise ValueError("Map not found.")


  # find shorted bombsite:
  closest_bombsite_area = float("Inf")

  bombinfo = dm.get_bomb_info(round_idx, frame_idx)
  ## todo: find closest area from bomb position

  ## todo: find bombsite area with minimum distance from bomb
  for a in NAV[map_name]:
    if area["areaName"].startswith("Bombsite"):


  geodesic_dist = area_distance(map_name=map_name, area_a=340, area_b=8773, dist_type="geodesic")

  ## todo: plot path from bomb to closest bombsite
  fig, ax = plot_map(map_name=map_name, map_type='simpleradar', dark=True)

  for a in NAV[map_name]:
    area = NAV[map_name][a]
    color = "None"
    if a in geodesic_dist["areas"]:
      color = "red"
    width = (area["southEastX"] - area["northWestX"])
    height = (area["northWestY"] - area["southEastY"])
    southwest_x = area["northWestX"]
    southwest_y = area["southEastY"]
    rect = patches.Rectangle((southwest_x, southwest_y), width, height, linewidth=1, edgecolor="yellow",
                             facecolor=color)
    ax.add_patch(rect)

  fig.show()



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
    rect = patches.Rectangle((northWestX, southEastY*10), width*10, height*10, linewidth=1, edgecolor="yellow",
                             facecolor=col)
    ax.add_patch(rect)
    if area["areaName"].startswith("Bombsite"):
      ax.text(northWestX*10, northWestY*10, str(a), fontsize=4, color="white")
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

  process_bomb_distance(dm, 5, 8, True)
