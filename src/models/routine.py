from dataclasses import dataclass, field
from typing import NewType

# This NewType exists to make sure we don't pass any kind of number in for FrameCount.
# When creating a value of type FrameCount, we must be expressly aware that this variable we're making represents a frame count.
FrameCount = NewType('FrameCount', int)

DEFAULT_ROUTINE_LENGTH = FrameCount(5)

@dataclass
class Routine:
    x: list[float] = field(default_factory=list)
    y: list[float] = field(default_factory=list)

    def add_point(self, x: float, y: float):
        """Adds a point to the routine."""
        self.x.append(x)
        self.y.append(y)
