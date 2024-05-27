
from collections import Counter

class PositionTracker:
    """A class for tracking the cumulative amount of times players enter each tile on the map, with a configurable tile size."""
    _map_name: str
    _tile_length: int
    _tile_activity_counter: Counter[tuple[int, int]]

    def __init__(self, map_name: str, tile_length: int):
        self._map_name = map_name
        self._tile_length = tile_length
        self._tile_activity_counter = Counter()
    
    @property
    def map_name(self) -> str:
        """The name of the map for which data is being tracked. Useful for ensuring that the correct map is being used in visualization or analysis."""
        return self._map_name
    
    @property
    def tile_length(self) -> int:
        """The length of each tile. As each tile is a square, this value is used for both the width and height of each tile."""
        return self._tile_length
    
    @property
    def tile_activity_counter(self) -> Counter[tuple[int, int]]:
        """The Counter object that keeps track of how many times each tile has been visited. The keys are tuples of the form (x, y) where x and y are the coordinates of the tile."""
        return self._tile_activity_counter

    def add_transformed_coordinates(self, x: float, y: float) -> int:
        """Increments the counter for the tile that the given player position coordinates fall into. Assumes that the given coordinates are already transformed to the correct map's coordinate system via the position_transform function from the awpy module.
        Returns the new count for the tile that the given coordinates fall into."""
        tile_x = int(x / self._tile_length)
        tile_y = int(y / self._tile_length)
        self._tile_activity_counter[(tile_x, tile_y)] += 1
        return self._tile_activity_counter[(tile_x, tile_y)]
    