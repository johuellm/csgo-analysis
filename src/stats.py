import csv
from pathlib import Path
from models.data_manager import DataManager
from metrics.map_control import process_map_control

EXAMPLE_DEMO_PATH = Path(__file__).parent / '../demos/esta/lan/de_dust2/00e7fec9-cee0-430f-80f4-6b50443ceacd.json'

KEYS_ROUND_LEVEL = ("roundNum", "isWarmup", "startTick", "freezeTimeEndTick", "endTick", "endOfficialTick", "bombPlantTick", "tScore", "ctScore", "endTScore", "endCTScore", "ctTeam", "tTeam", "winningSide", "winningTeam", "losingTeam", "roundEndReason", "ctFreezeTimeEndEqVal", "ctRoundStartEqVal", "ctRoundSpendMoney", "ctBuyType", "tFreezeTimeEndEqVal", "tRoundStartEqVal", "tRoundSpendMoney", "tBuyType")
#"parseKillFrame"
KEYS_FRAME_LEVEL = ("tick", "seconds", "clockTime")
KEYS_TEAM_LEVEL = ("side", "teamName", "teamEqVal", "alivePlayers", "totalUtility")
# "inventory", "spotters",
KEYS_PLAYER_LEVEL = ("steamID", "name", "team", "side", "x", "y", "z", "velocityX", "velocityY", "velocityZ", "viewX", "viewY", "hp", "armor", "activeWeapon", "totalUtility", "isAlive", "isBlinded", "isAirborne", "isDucking", "isDuckingInProgress", "isUnDuckingInProgress", "isDefusing", "isPlanting", "isReloading", "isInBombZone", "isInBuyZone", "isStanding", "isScoped", "isWalking", "isUnknown", "equipmentValue", "equipmentValueFreezetimeEnd", "equipmentValueRoundStart", "cash", "cashSpendThisRound", "cashSpendTotal", "hasHelmet", "hasDefuse", "hasBomb", "ping", "zoomLevel")



def process_round(round_idx):
  rows_round = []
  round = dm.get_game_round(round_idx)
  data_roundlevel = [round[key] for key in KEYS_ROUND_LEVEL]
  frames = dm._get_frames(round_idx)
  for frame in frames:
    data_framelevel = [frame[key] for key in KEYS_FRAME_LEVEL]

    team = frame["t"]
    data_teamlevel = [team[key] for key in KEYS_TEAM_LEVEL]
    for player in team["players"]:
      data_playerlevel = [player[key] for key in KEYS_PLAYER_LEVEL]
      row = data_roundlevel + data_framelevel + data_teamlevel + data_playerlevel
      rows_round.append(row)

    team = frame["ct"]
    data_teamlevel = [team[key] for key in KEYS_TEAM_LEVEL]
    for player in team["players"]:
      data_playerlevel = [player[key] for key in KEYS_PLAYER_LEVEL]
      row = data_roundlevel + data_framelevel + data_teamlevel + data_playerlevel
      rows_round.append(row)
  return(rows_round)



def process_metrics(round_idx):
  process_map_control(dm, round_idx)



if __name__ == '__main__':
  dm = DataManager(EXAMPLE_DEMO_PATH, do_validate=False)
  print("Match Id: %s with %d rounds" % (dm.get_match_id(), dm.get_round_count()))

  rows = []
  for round in range(dm.get_round_count()):
    print("Converting round %d" % round)
    rows.extend(process_round(round))

  with open("stats/testdemo.csv", 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(KEYS_ROUND_LEVEL + KEYS_FRAME_LEVEL + KEYS_TEAM_LEVEL + KEYS_PLAYER_LEVEL)
    writer.writerows(rows)
    print("%d rows written." % len(rows))
