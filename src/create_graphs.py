from metrics.base_metric import BaseMetric
from metrics.bomb_distance_metric import BombDistanceMetric
from metrics.distance_metric import DistanceMetric
from metrics.map_control_metric import MapControlMetric
from metrics.teamhp_metric import TeamHpMetric
from metrics.velocity_deviation_metric import VelocityDeviationMetric
from models.data_manager import DataManager
import stats


def process_round(dm: DataManager, round_idx: int, metrics: list[BaseMetric]) -> list[list[Any]]:
  rows_round = []
  round = dm.get_game_round(round_idx)

  # all variables on the round level --> graph data
  data_roundlevel = [round[key] for key in KEYS_ROUND_LEVEL]

  frames = dm._get_frames(round_idx)
  logger.info("Processing round %d with %d frames." % (round_idx, len(frames)))

  # store crucial bomb events for later analysis and estimating correct round ingame seconds.
  # all variables on the
  bomb_data = process_bomb_data(round)
  data_bomblevel = [bomb_data[key] for key in KEYS_BOMB_LEVEL]

  # iterate and process each frame
  for frame_idx, frame in enumerate(frames):


    #### TODO
    # create graph from values
    # nodes: 5 players, 2 target sites, 1 bomb
    # edges: distance between each node
    # node attributes: health, resources, etc.
    



    # check validity of frame
    valid_frame, err_text = check_frame_validity(frame)
    if not valid_frame:
      logger.warning("Skipping frame %d entirely because %s." % (frame_idx, err_text))
      continue

    # all variables on the frame level, they are added to each player observation later.
    data_framelevel = [frame[key] for key in KEYS_FRAME_LEVEL]

    # include estimated seconds from bomb data for each frame
    if bomb_data["bombTick"] != None and frame["tick"] >= bomb_data["bombTick"]:
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
    data_teamlevel_t = [team[key] for key in KEYS_TEAM_LEVEL]
    data_playerlevel_t = []
    # iterate through all players, but keep them in same order every iteration
    for player_idx, player in enumerate(sorted(team["players"], key=lambda p: dm.get_player_idx_mapped(p["name"], "t", frame))):
      data_playerlevel_t.extend([player[key] for key in KEYS_PLAYER_LEVEL])

    # all variables on the team and player level for the CT side
    team = frame["ct"]
    data_teamlevel_ct = [team[key] for key in KEYS_TEAM_LEVEL]
    data_playerlevel_ct = []
    # iterate through all players, but keep them in same order every iteration
    for player_idx, player in enumerate(sorted(team["players"], key=lambda p: dm.get_player_idx_mapped(p["name"], "ct", frame))):
      data_playerlevel_ct.extend([player[key] for key in KEYS_PLAYER_LEVEL])

    row = (data_roundlevel + data_bomblevel + data_framelevel + data_metriclevel
           + data_teamlevel_t + data_playerlevel_t + data_teamlevel_ct + data_playerlevel_ct)
    rows_round.append(row)
  return rows_round



def main():
  dm = DataManager(stats.EXAMPLE_DEMO_PATH, do_validate=False)
  output_filename = "testgraphs.csv"
  stats.logger.info("Processing match id: %s with %d rounds to file %s." % (dm.get_match_id(), dm.get_round_count(), output_filename))

  # with open(output_filename, 'w', newline='') as csvfile:
  #   writer = csv.writer(csvfile)
  #   writer.writerow(stats.generate_csv_header())

  #   rows_total = 0
  #   for round_idx in range(dm.get_round_count()):
  #     stats.logger.info("Converting round %d" % round_idx)

  #     # we need to swap mappings, because player sides switch here.
  #     # WARNING: This only works if teams player in MR15 setting.
  #     if round_idx == 15:
  #       dm.swap_player_mapping()

  #     # Write straight to file, so in case of error not all converted rows are lost.
  #     rows = stats.process_round(dm, round_idx, [
  #       BombDistanceMetric(), MapControlMetric(), DistanceMetric(cumulative=True), DistanceMetric(cumulative=False),
  #       VelocityDeviationMetric(), TeamHpMetric('t'), TeamHpMetric('ct')
  #     ])
  #     writer.writerows(rows)
  #     stats.logger.info("%d rows written to file." % len(rows))
  #     rows_total+= len(rows)
  #   stats.logger.info("SUCCESSFULLY COMPLETED: %d written in total." % rows_total)


if __name__ == '__main__':
	main()
