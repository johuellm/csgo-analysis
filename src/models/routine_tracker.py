from collections import defaultdict, Counter
from typing import overload
from models.routine import DEFAULT_ROUTINE_LENGTH, Routine
from awpy.visualization.plot import position_transform

class TilizedRoutine(Routine):
    """An extension of the Routine class that includes the tilized x and y values for the routine - that is, the x and y values transformed into tile coordinates."""
    _tile_length: int
    _tilized_x: list[int] # The x values of the routine transformed into tile coordinates.
    _tilized_y: list[int] # The y values of the routine transformed into tile coordinates.

    def __init__(self, routine: Routine, tile_length: int):
        super().__init__(routine.player_name, routine.team, routine.map_name, list(zip(routine.x, routine.y)))
        self._tile_length = tile_length
        # Transforming coordinates now as bucketing them into tiles and then transforming tile coordinates sounds like it would be less accurate - not sure if this feeling is true, though.
        self._tilized_x = [int(position_transform(routine.map_name, x, 'x') / tile_length) for x in routine.x]
        self._tilized_y = [int(position_transform(routine.map_name, y, 'y') / tile_length) for y in routine.y]

    @property
    def tile_length(self) -> int:
        """The length of each tile. As each tile is a square, this value is used for both the width and height of each tile."""
        return self._tile_length
    
    @property
    def tilized_x(self) -> list[int]:
        """Returns a list of x values for the routine transformed into tile coordinates."""
        return self._tilized_x
    
    @property
    def tilized_y(self) -> list[int]:
        """Returns a list of y values for the routine transformed into tile coordinates."""
        return self._tilized_y
    
    @overload
    def __getitem__(self, index: int) -> tuple[int, int]:
        """Returns the tilized x and y values at the given index."""
        ...

    @overload
    def __getitem__(self, index: slice) -> list[tuple[int, int]]:
        """Returns a list of tilized x and y value tuples at the given slice."""
        ...

    def __getitem__(self, index: int | slice) -> tuple[int, int] | list[tuple[int, int]]:
        """Determines which indexing method to use based on the value of the index parameter and returns the correct amount of x and y tuple values"""
        if isinstance(index, int):
            return self._tilized_x[index], self._tilized_y[index]
        elif isinstance(index, slice):
            return list(zip(self._tilized_x[index.start:index.stop:index.step], self._tilized_y[index.start:index.stop:index.step]))
        else:
            raise TypeError("Index must be an integer or slice.")
    
    # I want TilizedRoutines that have the same sequence of tilized x and y values to be considered equal, for set operations.
    def __hash__(self) -> int:
        return hash((tuple(self._tilized_x), tuple(self._tilized_y)))
    
    def __eq__(self, other: 'TilizedRoutine') -> bool:
        return self._tilized_x == other.tilized_x and self._tilized_y == other.tilized_y


class RoutineTracker:
    _map_name: str
    _tile_length: int
    _routine_length: int
    _tile_routine_counter: defaultdict[tuple[int, int], Counter[TilizedRoutine]] # A mapping from tile coordinates to a Counter object for tracking the number of times a routine starting from that tile has been counted.

    def __init__(self, map_name: str, tile_length: int, routine_length: int = DEFAULT_ROUTINE_LENGTH):
        self._map_name = map_name
        self._tile_length = tile_length
        self._routine_length = routine_length
        self._tile_routine_counter = defaultdict(Counter)

    @property
    def map_name(self) -> str:
        """The name of the map for which data is being tracked. 
        Useful for ensuring that the correct map is being used in visualization or analysis."""
        return self._map_name
    
    @property
    def tile_length(self) -> int:
        """The length of each tile. As each tile is a square, this value is used for both the width and height of each tile."""
        return self._tile_length
    
    @property
    def routine_length(self) -> int:
        """The length of each routine that is being tracked."""
        return self._routine_length
    
    @property
    def tile_routine_counter(self) -> dict[tuple[int, int], Counter[TilizedRoutine]]:
        """The dictionary mapping tile coordinates to Counter objects that keep track of how many times each routine was taken from that tile."""
        return self._tile_routine_counter
    
    def add_routine(self, routine: TilizedRoutine) -> int:
        """Increments the counter for the tile that the given routine's starting position falls into. 
        The position values stored in the routine object are assumed to be transformed into the map's coordinate system via the position_transform function from the awpy module.
        Returns the new count."""

        tile_x, tile_y = routine[0]
        self._tile_routine_counter[(tile_x, tile_y)][routine] += 1
        return self._tile_routine_counter[(tile_x, tile_y)][routine]
    
    def __len__(self) -> int:
        """Returns the total number of routines tracked by the RoutineTracker."""
        return sum(sum(counter.values()) for counter in self._tile_routine_counter.values())
