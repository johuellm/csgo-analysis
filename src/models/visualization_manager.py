from matplotlib.collections import PathCollection
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from awpy.visualization.plot import plot_map, position_transform
from matplotlib.lines import Line2D

from models.data_manager import DataManager
from models.routine import Routine
from models.team_type import TeamType

class VisualizationManager:
    dm: DataManager
    fig: Figure
    axes: Axes
    lines: list[Line2D] # Tracks lines for precise removal
    path_collections: list[PathCollection] # Tracks scatter plot points for precise removal

    def __init__(self, dm: DataManager, fig: Figure, axes: Axes):
        self.dm = dm
        self.fig = fig
        self.axes = axes
        self.lines = list()
        self.path_collections = list()
    
    @classmethod
    def from_data_manager(cls, dm: DataManager) -> 'VisualizationManager':
        """Create a VisualizationManager object from an instantiated DataManager object."""
        fig, axes = plot_map(
            map_name=dm.get_map_name(),
            map_type='simpleradar',
            dark=True
        )
        return cls(dm, fig, axes)

    def render(self):
        """Render the map. Primarily for use in CLI contexts."""
        self.fig.show()

    def draw_routine(self, routine: Routine, fmt: str = "", **kwargs) -> Axes:
        """Draws a routine on the map. `fmt` is a format string following matplotlib fmt string notation, and kwargs can be used to add additional format options (overwriting any conflicting options from the format string)."""

        map_name = self.dm.get_map_name()

        transformed_x = [position_transform(map_name, xpos, 'x') for xpos in routine.x]
        transformed_y = [position_transform(map_name, ypos, 'y') for ypos in routine.y]

        line = self.axes.plot(transformed_x, transformed_y, fmt, **kwargs)
        self.lines.extend(line)
        return self.axes
    
    def __clear_all_drawings(self):
        """Clears all drawings from the figure."""
        for line in self.lines:
            line.remove()
        self.lines.clear()
        for collection in self.path_collections:
            collection.remove()
        self.path_collections.clear()
    
    def draw_round_start(self, round_index: int) -> Axes:
        """Draws the positions of players at the start of a round. Raises a ValueError if the round index is out of bounds."""
        round_count = self.dm.get_round_count()
        if round_index > round_count - 1:
            raise ValueError(f"Round index {round_index} out of bounds (max index is {round_count - 1})")
        
        self.__clear_all_drawings()

        player_info_lists = self.dm._get_player_info_lists(round_index, 0)
        t_side_players = player_info_lists[TeamType.T]
        ct_side_players = player_info_lists[TeamType.CT]

        map_name = self.dm.get_map_name()

        transformed_t_x = [position_transform(map_name, player['x'], 'x') for player in t_side_players]
        transformed_t_y = [position_transform(map_name, player['y'], 'y') for player in t_side_players]

        self.path_collections.append(self.axes.scatter(transformed_t_x, transformed_t_y, c='goldenrod'))

        transformed_ct_x = [position_transform(map_name, player['x'], 'x') for player in ct_side_players]
        transformed_ct_y = [position_transform(map_name, player['y'], 'y') for player in ct_side_players]

        self.path_collections.append(self.axes.scatter(transformed_ct_x, transformed_ct_y, c='lightblue'))
        return self.axes
