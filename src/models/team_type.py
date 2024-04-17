from enum import Enum

class TeamType(Enum):
    CT = "ct"
    T = "t"

    @classmethod
    def from_str(cls, team_str: str) -> 'TeamType':
        """Converts a string to a TeamType enum, raising a ValueError if the string is not one of the valid two team types."""
        if team_str == "ct":
            return cls.CT
        elif team_str == "t":
            return cls.T
        else:
            raise ValueError(f"Invalid team type: {team_str}")
