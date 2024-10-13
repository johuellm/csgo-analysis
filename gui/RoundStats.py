from Player import Player
class RoundStats:
  def __init__(self, stats: dict):
    self.players = [Player(**stats[0]), Player(**stats[1]), Player(**stats[2]), Player(**stats[3]), Player(**stats[4])]
    self.winningSide = stats["winningSide"]
    self.roundEndReason = stats["roundEndReason"]
    self.opponentsAlive = stats["alivePlayers"]
    self.opponentEquipmentValue = stats["teamEqVal"]
    self.clocktime = stats["clockTime"]