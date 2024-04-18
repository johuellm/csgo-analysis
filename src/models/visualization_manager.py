from matplotlib.figure import Figure
from matplotlib.axes import Axes
from awpy.visualization.plot import plot_map, position_transform

from models.routine import Routine

class VisualizationManager:
    fig: Figure
    axes: Axes
    map: str

    def __init__(self, fig: Figure, axes: Axes, map: str):
        self.fig = fig
        self.axes = axes
        self.map = map
    
    @classmethod
    def from_map(cls, map_name: str) -> 'VisualizationManager':
        """Create a VisualizationManager object from a map name."""
        fig, axes = plot_map(
            map_name=map_name,
            map_type='simpleradar',
            dark=True
        )
        return cls(fig, axes, map_name)

    def render(self):
        """Render the map. Primarily for use in CLI contexts."""
        self.fig.show()

    def draw_routine(self, routine: Routine, fmt: str | None = None, **kwargs) -> Axes:
        """Draws a routine on the map. `fmt` is a format string following matplotlib fmt string notation, and kwargs can be used to add additional format options."""

        transformed_x = [position_transform(self.map, xpos, 'x') for xpos in routine.x]
        transformed_y = [position_transform(self.map, ypos, 'y') for ypos in routine.y]

        self.axes.plot(transformed_x, transformed_y, fmt, **kwargs)
        return self.axes
