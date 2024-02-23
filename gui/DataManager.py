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
    routinesT = [[Routine.Routine([],[]) for _ in range(numberChunks)] for _ in range(5)]
    routinesCT = [[Routine.Routine([],[]) for _ in range(numberChunks)] for _ in range(5)]

    for chunkId, chunk in enumerate(frameChunks):
      for frameId, frame in enumerate(chunk):
        if frameId == 0:
          firstFrame = frame["seconds"]
        elif frameId == len(chunk)-1:
          chunkElapsedTime = frame["seconds"] - firstFrame
          # print("Chunk #%d Elapsed Time: %f" % (chunkId, chunkElapsedTime))

        for playerIndex, player in enumerate(frame["t"]["players"]):
          routinesT[playerIndex][chunkId].x.append(player["x"])
          routinesT[playerIndex][chunkId].y.append(player["y"])
        for playerIndex, player in enumerate(frame["ct"]["players"]):
          routinesCT[playerIndex][chunkId].x.append(player["x"])
          routinesCT[playerIndex][chunkId].y.append(player["y"])

    return Team.Team(routinesT), Team.Team(routinesCT)
