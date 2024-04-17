from dataclasses import dataclass, field

DEFAULT_ROUTINE_LENGTH = 5

@dataclass
class Routine:
    x: list[float] = field(default_factory=list)
    y: list[float] = field(default_factory=list)

    def add_point(self, x: float, y: float):
        """Adds a point to the routine."""
        self.x.append(x)
        self.y.append(y)
