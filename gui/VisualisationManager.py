import numpy as np
import Routine
from awpy.visualization.plot import plot_map, position_transform

class VisualisationManager:
  def __init__(self, fig=None, axes=None, map=None):
    self.fig = fig
    self.axes = axes
    self.map = map

  def Render(self):
    self.fig.show()

  def DrawMap(self, mapName=map):
    self.map = mapName
    self.fig, self.axes = plot_map(map_name=self.map, map_type="simpleradar", dark=True)
    return self.fig, self.axes

  def DrawRoutine(self, routine: Routine.Routine, fmt='o-r'):
    # alternative: position_transform_all
    transformed_x = [
      position_transform(self.map, xpos, "x")
      for xpos in routine.x
    ]
    transformed_y = [
      position_transform(self.map, ypos, "y")
      for ypos in routine.y
    ]
    # self.axes.scatter(transformed_x, transformed_y, s=2)
    # self.axes = self.axes.plot(transformed_x, transformed_y, 'o-r')
    self.axes.plot(transformed_x, transformed_y, fmt)
    return self.axes

  def DrawTeamRoutine(self, timepoint: int, team):
    pass

  def DrawPlayerRoutine(self, timepoint: int, player):
    pass

