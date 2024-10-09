import csv
import logging
import os
from pathlib import Path
from typing import Any

from metrics.base_metric import BaseMetric
from metrics.bomb_distance_metric import BombDistanceMetric
from metrics.map_control_metric import MapControlMetric
from models.data_manager import DataManager

if os.environ.get("LOGGING_INFO"):
  logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EXAMPLE_DEMO_PATH = Path(__file__).parent / '../demos/esta/lan/de_dust2/00e7fec9-cee0-430f-80f4-6b50443ceacd.json'

KEYS_ROUND_LEVEL = ("roundNum", "isWarmup", "startTick", "freezeTimeEndTick", "endTick", "endOfficialTick", "bombPlantTick", "tScore", "ctScore", "endTScore", "endCTScore", "ctTeam", "tTeam", "winningSide", "winningTeam", "losingTeam", "roundEndReason", "ctFreezeTimeEndEqVal", "ctRoundStartEqVal", "ctRoundSpendMoney", "ctBuyType", "tFreezeTimeEndEqVal", "tRoundStartEqVal", "tRoundSpendMoney", "tBuyType")
#"parseKillFrame"
KEYS_FRAME_LEVEL = ("tick", "seconds", "clockTime")
KEYS_METRIC_LEVEL = ("bombDistance", "mapControl")
KEYS_TEAM_LEVEL = ("side", "teamName", "teamEqVal", "alivePlayers", "totalUtility")
# "inventory", "spotters",
KEYS_PLAYER_LEVEL = ("steamID", "name", "team", "side", "x", "y", "z", "velocityX", "velocityY", "velocityZ", "viewX", "viewY", "hp", "armor", "activeWeapon", "totalUtility", "isAlive", "isBlinded", "isAirborne", "isDucking", "isDuckingInProgress", "isUnDuckingInProgress", "isDefusing", "isPlanting", "isReloading", "isInBombZone", "isInBuyZone", "isStanding", "isScoped", "isWalking", "isUnknown", "equipmentValue", "equipmentValueFreezetimeEnd", "equipmentValueRoundStart", "cash", "cashSpendThisRound", "cashSpendTotal", "hasHelmet", "hasDefuse", "hasBomb", "ping", "zoomLevel")



def process_round(round_idx: int, metrics: list[BaseMetric]) -> list[list[Any]]:
  rows_round = []
  round = dm.get_game_round(round_idx)
  data_roundlevel = [round[key] for key in KEYS_ROUND_LEVEL]
  frames = dm._get_frames(round_idx)
  logger.info("Processing round %d with %d frames." % (round_idx, len(frames)))
  for frame_idx, frame in enumerate(frames):
    # all variables on the frame level, they are added to each player observation later.
    data_framelevel = [frame[key] for key in KEYS_FRAME_LEVEL]

    # all estimated metrics, they are added to each player observation later
    data_metriclevel = [metric.process_metric_frame(dm, round_idx, frame_idx) for metric in metrics]

    # all variables on the team and player level for the T side
    team = frame["t"]
    data_teamlevel = [team[key] for key in KEYS_TEAM_LEVEL]
    for player in team["players"]:
      data_playerlevel = [player[key] for key in KEYS_PLAYER_LEVEL]
      row = data_roundlevel + data_framelevel + data_metriclevel + data_teamlevel + data_playerlevel
      rows_round.append(row)

    # all variables on the team and player level for the CT side
    team = frame["ct"]
    data_teamlevel = [team[key] for key in KEYS_TEAM_LEVEL]
    for player in team["players"]:
      data_playerlevel = [player[key] for key in KEYS_PLAYER_LEVEL]
      row = data_roundlevel + data_framelevel + data_metriclevel + data_teamlevel + data_playerlevel
      rows_round.append(row)
  return rows_round



if __name__ == '__main__':
  dm = DataManager(EXAMPLE_DEMO_PATH, do_validate=False)
  logger.info("Processing match id: %s with %d rounds." % (dm.get_match_id(), dm.get_round_count()))

  rows = []
  for round in range(1,2): #dm.get_round_count()):
    logger.info("Converting round %d" % round)
    rows.extend(process_round(round, [BombDistanceMetric(), MapControlMetric()]))

  with open("metrics/testdemo.csv", 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(KEYS_ROUND_LEVEL + KEYS_FRAME_LEVEL + KEYS_METRIC_LEVEL + KEYS_TEAM_LEVEL + KEYS_PLAYER_LEVEL)
    writer.writerows(rows)
    logger.info("%d rows written." % len(rows))
