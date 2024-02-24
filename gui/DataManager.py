import json
import numpy as np
import Team, Routine

class DataManager:
  def __init__(self):
    self.data = None

  def LoadData(self, path: str):
    with open(path) as fp:
      self.data = json.load(fp)

  def GetGameRound(self, roundId: int):
    return self.data['gameRounds'][roundId]

  def GetFrame(self, roundId: int, frameId: int):
    return self.data['gameRounds'][roundId]["frames"][frameId]

  def GetMap(self):
    return self.data["mapName"]

  def GetAllTeamRoutines(self, roundId: int, routineLength: int):
    frames = self.GetGameRound(roundId)["frames"]
    frameChunks = np.split(frames, np.arange(routineLength, len(frames), routineLength))
    numberChunks = len(frameChunks)

    playerRoutinesT = dict((playerName,  # key is player name
                            [Routine.Routine([], []) for _ in range(numberChunks)])  # value is list of routines
                            for playerName in [player["name"] for player in frames[0]["t"]["players"]])  # list comprehension to retrieve unique player names
    playerRoutinesCT = dict((playerName,  # key is player name
                             [Routine.Routine([], []) for _ in range(numberChunks)])  # value is list of routines
                            for playerName in [player["name"] for player in frames[0]["ct"]["players"]])  # list comprehension to retrieve unique player names

    for chunkId, chunk in enumerate(frameChunks):
      for frameId, frame in enumerate(chunk):

        for playerIndex, player in enumerate(frame["t"]["players"]):
          playerRoutinesT[player["name"]][chunkId].x.append(player["x"])
          playerRoutinesT[player["name"]][chunkId].y.append(player["y"])

        for playerIndex, player in enumerate(frame["ct"]["players"]):
          playerRoutinesCT[player["name"]][chunkId].x.append(player["x"])
          playerRoutinesCT[player["name"]][chunkId].y.append(player["y"])

    return Team.Team(list(playerRoutinesT.values())), Team.Team(list(playerRoutinesCT.values()))
