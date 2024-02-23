from Routine import Routine

class Team:
  def __init__(self, routines: list):
    self.routines1 = routines[0]
    self.routines2 = routines[1]
    self.routines3 = routines[2]
    self.routines4 = routines[3]
    self.routines5 = routines[4]

  def GetRoutines(self):
    return [self.routines1, self.routines2, self.routines3, self.routines4, self.routines5]

  def GetRoutinesPlayer(self, playerId: int):
    return self.GetRoutines()[playerId]
