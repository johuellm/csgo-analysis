from dataclasses import dataclass
from typing import NewType, overload

from models.team_type import TeamType

# This NewType exists to make sure we don't pass any kind of number in for FrameCount.
# When creating a value of type FrameCount, we must be expressly aware that this variable we're making represents a frame count.
FrameCount = NewType('FrameCount', int)

DEFAULT_ROUTINE_LENGTH = FrameCount(5)

@dataclass(eq=False)
class Routine:
    """A class representing a player's trajectory - that is, multiple points ."""
    player_name: str
    team: TeamType
    _x: list[float]
    _y: list[float]

    def __init__(self, player_name: str, team: TeamType, x_values: list[float] | None = None, y_values: list[float] | None = None):
        self.player_name = player_name
        self.team = team
        if x_values is None: x_values = list()
        if y_values is None: y_values = list()
        if len(x_values) != len(y_values):
            raise ValueError("The provided lists of x and y values must be the same length.")
        self._x = x_values
        self._y = y_values

    @property
    def x(self) -> list[float]:
        """Returns a list of x values for the routine."""
        return self._x
    
    @property
    def y(self) -> list[float]:
        """Returns a list of y values for the routine."""
        return self._y

    def length(self) -> int:
        """Returns the length of the routine."""
        return len(self._x)
    
    def add_point(self, x: float, y: float):
        """Adds a point to the routine."""
        self.x.append(x)
        self.y.append(y)

    @overload
    def __getitem__(self, index: int) -> tuple[float, float]:
        """Returns the x and y values at the given index."""
        ...

    @overload
    def __getitem__(self, index: slice) -> list[tuple[float, float]]:
        """Returns a list of x and y value tuples at the given slice."""
        ...

    def __getitem__(self, index: int | slice) -> tuple[float, float] | list[tuple[float, float]]:
        """Determines which indexing method to use based on the value of the index parameter and returns the correct amount of x and y tuple values"""
        if isinstance(index, int):
            return self._x[index], self._y[index]
        elif isinstance(index, slice):
            return list(zip(self._x[index.start:index.stop:index.step], self._y[index.start:index.stop:index.step]))
        else:
            raise TypeError("Index must be an integer or slice.")
