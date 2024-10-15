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

## WARNING: (1) ESTA demos are parsed at 2 Hz or 2 frames per in-game second
## WARNING: (2) seconds and clocktime are reset after plant
## WARNING: (3) player indices vary between frames
EXAMPLE_DEMO_PATH = Path(__file__).parent / '../demos/esta/lan/de_dust2/00e7fec9-cee0-430f-80f4-6b50443ceacd.json'

KEYS_ROUND_LEVEL = ("roundNum", "isWarmup", "startTick", "freezeTimeEndTick", "endTick", "endOfficialTick", "bombPlantTick", "tScore", "ctScore", "endTScore", "endCTScore", "ctTeam", "tTeam", "winningSide", "winningTeam", "losingTeam", "roundEndReason", "ctFreezeTimeEndEqVal", "ctRoundStartEqVal", "ctRoundSpendMoney", "ctBuyType", "tFreezeTimeEndEqVal", "tRoundStartEqVal", "tRoundSpendMoney", "tBuyType")
#"parseKillFrame"
KEYS_BOMB_LEVEL = ("bombTick", "bombSeconds", "bombClockTime", "bombPlayerSteamID", "bombPlayerName", "bombPlayerTeam", "bombPlayerX", "bombPlayerY", "bombPlayerZ", "bombAction", "bombSite")
KEYS_FRAME_LEVEL = ("tick", "seconds", "clockTime", "bombPlanted", "secondsCalculated")
KEYS_METRIC_LEVEL = ("bombDistance", "mapControl", "totalDistance", "deltaDistance")
KEYS_TEAM_LEVEL = ("side", "teamName", "teamEqVal", "alivePlayers", "totalUtility")
# "inventory", "spotters", "isBlinded", "isAirborne", "isDucking", "isDuckingInProgress", "isUnDuckingInProgress", "isStanding", "isScoped", "isWalking", "isUnknown", "ping", "zoomLevel"
KEYS_PLAYER_LEVEL = ("steamID", "name", "team", "side", "x", "y", "z", "velocityX", "velocityY", "velocityZ", "viewX", "viewY", "hp", "armor", "activeWeapon", "totalUtility", "isAlive", "isDefusing", "isPlanting", "isReloading", "isInBombZone", "isInBuyZone", "equipmentValue", "equipmentValueFreezetimeEnd", "equipmentValueRoundStart", "cash", "cashSpendThisRound", "cashSpendTotal", "hasHelmet", "hasDefuse", "hasBomb")



def process_round(dm: DataManager, round_idx: int, metrics: list[BaseMetric]) -> list[list[Any]]:
  rows_round = []
  round = dm.get_game_round(round_idx)

  # all variables on the round level
  data_roundlevel = [round[key] for key in KEYS_ROUND_LEVEL]

  frames = dm._get_frames(round_idx)
  logger.info("Processing round %d with %d frames." % (round_idx, len(frames)))

  # store crucial bomb events for later analysis and estimating correct round ingame seconds.
  # all variables on the
  bomb_data = process_bomb_data(round)
  data_bomblevel = [bomb_data[key] for key in KEYS_BOMB_LEVEL]

  # iterate and process each frame
  for frame_idx, frame in enumerate(frames):

    # check validity of frame
    valid_frame, err_text = check_frame_validity(frame)
    if not valid_frame:
      logger.warning("Skipping frame %d entirely because %s." % (frame_idx, err_text))
      continue

    # all variables on the frame level, they are added to each player observation later.
    data_framelevel = [frame[key] for key in KEYS_FRAME_LEVEL]

    # include estimated seconds from bomb data for each frame
    if bomb_data != None and frame["tick"] >= bomb_data["bombTick"]:
      data_framelevel.append(frame["seconds"] + bomb_data["bombSeconds"])
    else:
      data_framelevel.append(frame["seconds"])

    # all estimated metrics, they are added to each player observation later
    ### todo some metrics need specific process_metric_round
    ### todo: distance metrics should also be estimated for CT side
    data_metriclevel = []
    for metric in metrics:
      try:
        metric_value = metric.process_metric_frame(dm, round_idx, frame_idx)
        data_metriclevel.append(metric_value)
      except (ValueError, KeyError, ZeroDivisionError) as err:
        ## TODO: Fix the ZeroDivisonError
        logger.warning(err)
        logger.warning("Ignoring metric for frame %d and adding NA instead for metric %s." % (frame_idx, metric.__class__))
        data_metriclevel.append(None)

    # all variables on the team and player level for the T side
    team = frame["t"]
    data_teamlevel = [team[key] for key in KEYS_TEAM_LEVEL]
    data_playerlevel = []
    # iterate through all players, but keep them in same order every iteration
    for player_idx, player in enumerate(sorted(team["players"], key=lambda p: dm.get_player_idx_mapped(p["name"], "t", frame))):
      data_playerlevel.extend([player[key] for key in KEYS_PLAYER_LEVEL])

    row = data_roundlevel + data_bomblevel + data_framelevel + data_metriclevel + data_teamlevel + data_playerlevel
    rows_round.append(row)

    # all variables on the team and player level for the CT side
    team = frame["ct"]
    data_teamlevel = [team[key] for key in KEYS_TEAM_LEVEL]
    data_playerlevel = []
    # iterate through all players, but keep them in same order every iteration
    for player_idx, player in enumerate(sorted(team["players"], key=lambda p: dm.get_player_idx_mapped(p["name"], "ct", frame))):
      data_playerlevel = [player[key] for key in KEYS_PLAYER_LEVEL]

    row = data_roundlevel + data_bomblevel + data_framelevel + data_metriclevel + data_teamlevel + data_playerlevel
    rows_round.append(row)
  return rows_round


def check_frame_validity(frame):
  if len(frame["t"]["players"]) != 5:
    return False, "Frame does not have 5 T-side players."

  if len(frame["ct"]["players"]) != 5:
    return False, "Frame does not have 5 T-side players."

  return True, None


def process_bomb_data(round):
  # initialize empty if bomb was not planted
  bomb_data = {
    "bombTick": None,
    "bombSeconds": None,
    "bombClockTime": None,
    "bombPlayerSteamID": None,
    "bombPlayerName": None,
    "bombPlayerTeam": None,
    "bombPlayerX": None,
    "bombPlayerY": None,
    "bombPlayerZ": None,
    "bombAction": None,
    "bombSite": None
  }
  for bomb_event in round["bombEvents"]:
    if bomb_event == "plant":
      bomb_data = {
        "bombTick": bomb_data["tick"],
        "bombSeconds": bomb_data["seconds"],
        "bombClockTime": bomb_data["clockTime"],
        "bombPlayerSteamID": bomb_data["playerSteamID"],
        "bombPlayerName": bomb_data["playerName"],
        "bombPlayerTeam": bomb_data["playerTeam"],
        "bombPlayerX": bomb_data["playerX"],
        "bombPlayerY": bomb_data["playerY"],
        "bombPlayerZ": bomb_data["playerZ"],
        "bombAction": bomb_data["bombAction"],
        "bombSite": bomb_data["bombSite"]
      }
  return bomb_data

def generate_keys_all_players():
  keys = []
  for player_idx in range(1,6):
    for key in KEYS_PLAYER_LEVEL:
      keys.append("p%d_%s" % (player_idx, key))
  return tuple(keys)


def main():
  dm = DataManager(EXAMPLE_DEMO_PATH, do_validate=False)
  output_filename = "testdemo.csv"
  logger.info("Processing match id: %s with %d rounds to file %s." % (dm.get_match_id(), dm.get_round_count(), output_filename))

  with open(output_filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(KEYS_ROUND_LEVEL + KEYS_BOMB_LEVEL + KEYS_FRAME_LEVEL + KEYS_METRIC_LEVEL + KEYS_TEAM_LEVEL + generate_keys_all_players())

    rows_total = 0
    for round in range(dm.get_round_count()):
      logger.info("Converting round %d" % round)

      # Write straight to file, so in case of error not all converted rows are lost.
      rows = process_round(round, [
        BombDistanceMetric(), MapControlMetric(), DistanceMetric(cumulative=True), DistanceMetric(cumulative=False)
      ])
      writer.writerows(rows)
      logger.info("%d rows written to file." % len(rows))
      rows_total+= len(rows)
    logger.info("SUCCESSFULLY COMPLETED: %d written in total." % rows_total)


def test_round_mapping():
  dm = DataManager(EXAMPLE_DEMO_PATH, do_validate=False)
  logger.info("Processing match id: %s with %d rounds to console." % (dm.get_match_id(), dm.get_round_count()))

  rows_total = 0
  logger.info("Converting round %d" % round)

  # Write straight to file, so in case of error not all converted rows are lost.
  rows = process_round(dm, 5, [
    BombDistanceMetric(), DistanceMetric(cumulative=True)
  ])
  rows_total+= len(rows)
  logger.info("SUCCESSFULLY COMPLETED: %d written in total." % rows_total)

if __name__ == '__main__':
  #main()
  test_round_mapping()
