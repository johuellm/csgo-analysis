from dataclasses import dataclass
from models.data_manager import TeamType
from player import Player

@dataclass
class RoundStats:
    players: list[Player]
    winning_side: TeamType
    round_end_reason: str # TODO: Maybe enum this
    opponents_alive: int
    opponent_equipment_value: int
    clock_time: str
