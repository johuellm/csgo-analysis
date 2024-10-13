import json
import numpy as np
import Team, Routine, RoundStats

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

  def GetPlayerRoutine(self, playerId: int, roundId: int, routineLength: int, frameId: int):
    frames = self.GetGameRound(roundId)["frames"]
    firstFrameId = frameId - routineLength
    if firstFrameId < 0:
      firstFrameId = 0
    chunkFrames = frames[firstFrameId:frameId]

    x, y = zip(*[(chunkFrame["t"]["players"][playerId]["x"],chunkFrame["t"]["players"][playerId]["y"]) for chunkFrame in chunkFrames])
    return Routine.Routine(x,y)

  def GetPlayerFromPlayers(self, players: list, playerId: int, teamId: str):
    mapping = self.mappingT if teamId == "t" else self.mappingCT
    for player in players:
      if player["name"] == mapping[playerId]:
        return player
    raise KeyError("CS:GO Player not found.")

  def GetPlayerAtFrame(self, playerId: int, teamId: str, roundId: int, frameId: int):
    players = self.GetGameRound(roundId)["frames"][frameId][teamId]["players"]
    player = self.GetPlayerFromPlayers(players, playerId, teamId)
    return player

  def GetPlayerAlive(self, playerId: int, teamId: str, roundId: int, frameId: int):
    return self.GetPlayerAtFrame(playerId, teamId, roundId, frameId)["isAlive"]

  def GetRoundStats(self, roundId: int, frameId: int):
    round = self.GetGameRound(roundId)

    # round-level stats
    roundStats = {k: round[k] for k in ("winningSide", "roundEndReason")}

    # frame-level stats
    roundStats["clockTime"] = round["frames"][frameId]["clockTime"]

    # ct team stats
    roundStats["alivePlayers"] = round["frames"][frameId]["ct"]["alivePlayers"]
    roundStats["teamEqVal"] = round["frames"][frameId]["ct"]["teamEqVal"]

    # t team stats
    for playerId in range(5):
      player = self.GetPlayerAtFrame(playerId, "t", roundId, frameId)
      roundStats[playerId] = {k: player[k] for k in ("isAlive", "hp", "activeWeapon", "equipmentValue")}

    return RoundStats.RoundStats(roundStats)

  def GetPlayerHealthPoints(self, playerId: int, teamId: str, roundId: int, frameId: int):
    return self.GetPlayerAtFrame(playerId, teamId, roundId, frameId)["hp"]

  def GetTeamRoutine(self, roundId: int, routineLength: int, frameId: int):
    pass


  def GetNumberRoutines(self, roundId: int, routineLength: int):
    pass


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

    # store id-name mapping for now until rewrite is complete
    self.mappingT = dict(zip(range(5),playerRoutinesT.keys()))
    self.mappingCT = dict(zip(range(5),playerRoutinesCT.keys()))

    return Team.Team(list(playerRoutinesT.values())), Team.Team(list(playerRoutinesCT.values()))
