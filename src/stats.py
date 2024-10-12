import csv
import logging
import os
from pathlib import Path
from typing import Any

from metrics.base_metric import BaseMetric
from metrics.bomb_distance_metric import BombDistanceMetric
from metrics.distance_metric import DistanceMetric
from metrics.map_control_metric import MapControlMetric
from models.data_manager import DataManager

LOGGING_LEVEL = os.environ.get("LOGGING_INFO")
if LOGGING_LEVEL == "INFO":
  logging.basicConfig(level=logging.INFO)
elif LOGGING_LEVEL == "DEBUG":
  logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

EXAMPLE_DEMO_PATH = Path(__file__).parent / '../demos/esta/lan/de_dust2/00e7fec9-cee0-430f-80f4-6b50443ceacd.json'

KEYS_ROUND_LEVEL = ("roundNum", "isWarmup", "startTick", "freezeTimeEndTick", "endTick", "endOfficialTick", "bombPlantTick", "tScore", "ctScore", "endTScore", "endCTScore", "ctTeam", "tTeam", "winningSide", "winningTeam", "losingTeam", "roundEndReason", "ctFreezeTimeEndEqVal", "ctRoundStartEqVal", "ctRoundSpendMoney", "ctBuyType", "tFreezeTimeEndEqVal", "tRoundStartEqVal", "tRoundSpendMoney", "tBuyType")
#"parseKillFrame"
KEYS_FRAME_LEVEL = ("tick", "seconds", "clockTime")
KEYS_METRIC_LEVEL = ("bombDistance", "mapControl", "totalDistance", "deltaDistance")
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
    ### todo some metrics need specific process_metric_round
    data_metriclevel = []
    for metric in metrics:
      try:
        metric_value = metric.process_metric_frame(dm, round_idx, frame_idx)
        data_metriclevel.append(metric_value)
      except (ValueError, KeyError, ZeroDivisionError) as err:
        ## TODO: Fix the ZeroDivisonError
        logger.warning(err)
        logger.warning("Ignoring frame %d and adding NA instead for metric %s." % (frame_idx, metric.__class__))
        data_metriclevel.append(None)

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
  output_filename = "testdemo.csv"
  logger.info("Processing match id: %s with %d rounds to file %s." % (dm.get_match_id(), dm.get_round_count(), output_filename))

  with open(output_filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(KEYS_ROUND_LEVEL + KEYS_FRAME_LEVEL + KEYS_METRIC_LEVEL + KEYS_TEAM_LEVEL + KEYS_PLAYER_LEVEL)

    # rows = []
    rows_total = 00
    for round in range(dm.get_round_count()):
      logger.info("Converting round %d" % round)

      # rows.extend(process_round(round, [
      #   BombDistanceMetric(), MapControlMetric(), DistanceMetric(cumulative=True), DistanceMetric(cumulative=False)
      # ]))

      # Write straight to file, so in case of error not all converted rows are lost.
      rows = process_round(round, [
        BombDistanceMetric(), MapControlMetric(), DistanceMetric(cumulative=True), DistanceMetric(cumulative=False)
      ])
      writer.writerows(rows)
      logger.info("%d rows written to file." % len(rows))
      rows_total+= len(rows)
    logger.info("SUCCESSFULLY COMPLETED: %d written in total." % rows_total)
