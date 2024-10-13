import json
import pandas as pd
import numpy as np

from awpy.visualization.plot import plot_frame_map_control, plot_map, position_transform

with open(r"/mnt/d/dev/csgo-analysis/demos/dust2/00e7fec9-cee0-430f-80f4-6b50443ceacd.json") as fp:
  data = json.load(fp)

fig, axes = plot_map(map_name=data['mapName'], map_type="simpleradar", dark=True)

frames = data['gameRounds'][16]["frames"]




positions_x = []
positions_y = []
player_ids = []
player_dict = {}
for frameIndex, frame in enumerate(frames):
  if frameIndex % 5 == 0:
    for playerIndex, player in enumerate(frame["t"]["players"]):
      positions_x.append(player["x"])
      positions_y.append(player["y"])
      player_ids.append(playerIndex)

# alternative: position_transform_all
transformed_x = [
  position_transform(data['mapName'], xpos, "x")
  for xpos in positions_x
]
transformed_y = [
  position_transform(data['mapName'], ypos, "y")
  for ypos in positions_y
]

colormap = np.array(['r', 'g', 'b' , 'y', 'c'])
# colormap does not work with line graph; segment before plot
axes.plot(transformed_x, transformed_y)
# axes.scatter(transformed_x, transformed_y, s=2, color=colormap[np.array(player_ids)])



fig.show()


