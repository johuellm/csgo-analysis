import json
import re
import time
from collections import defaultdict
from collections.abc import Generator
from datetime import datetime, timedelta
from pathlib import Path

from awpy.types import BombInfo, Game, GameFrame, GameRound, GrenadeAction, PlayerInfo
from pydantic import TypeAdapter, ValidationError

from datamodel.player import Player
from datamodel.round_events import RoundActions
from datamodel.round_stats import RoundStats
from datamodel.routine import FrameCount, Routine
from datamodel.side_type import SideType
from datamodel.team_names import TeamNames
from datamodel.team_routines import BothTeamsRoutines, TeamRoutines
from datamodel.team_scores import TeamScore

# Path to a demo file for testing
EXAMPLE_DEMO_PATH = (
    Path(__file__).parent / "../../demos/esta/0013db25-4444-452b-980b-7702dc6fb810.json"
)

# For validating JSON data as a Game object
game_validator = TypeAdapter(Game)


# This function exists outside of DataManager in case we want to use it elsewhere
def _load_game_data(file_path: Path, do_validate: bool = True, logger=None) -> Game:
    """Loads a JSON file containing a Game object. If `do_validate` is True, the data will be validated against the Game schema."""

    def is_valid_player(p: dict) -> bool:
        required_fields = [
            "eyeX",
            "eyeY",
            "eyeZ",
            "flashGrenades",
            "smokeGrenades",
            "heGrenades",
            "fireGrenades",
            "lastPlaceName",
            "isBot",
        ]
        return all(field in p for field in required_fields)

    def is_valid_frame(frame: dict) -> bool:
        return (
            isinstance(frame.get("frameID"), int)
            and isinstance(frame.get("globalFrameID"), int)
            and isinstance(frame.get("clockTime"), str)
        )

    def sanitize_game_data(game_data: dict, file_path: Path) -> dict:
        # Drop root-level fields if missing
        required_root_keys = ["chatMessages", "parserParameters"]
        for key in required_root_keys:
            game_data.setdefault(key, {} if key == "parserParameters" else [])

        # Ensure required nested parser fields
        game_data["parserParameters"].setdefault("parseChat", False)

        # Add missing matchID from file name if not present
        game_data.setdefault("matchID", file_path.stem)

        for rnd in game_data.get("gameRounds", []):
            if "frames" in rnd:
                rnd["frames"] = [
                    frame for frame in rnd["frames"] if is_valid_frame(frame)
                ]
                for frame in rnd["frames"]:
                    for side in ("ct", "t"):
                        if side in frame and "players" in frame[side]:
                            frame[side]["players"] = [
                                p for p in frame[side]["players"] if is_valid_player(p)
                            ]
            if "kills" in rnd:
                for kill in rnd["kills"]:
                    kill.setdefault("playerTradedSide", None)

        return game_data

    with open(file_path) as file:
        try:
            data = json.load(file)
            if do_validate:
                data = sanitize_game_data(data, file_path)
                if logger:
                    logger.info(
                        f"Validating demo data against Game schema for file {file_path.name}"
                    )
                else:
                    print(
                        f"Validating demo data against Game schema for file {file_path.name}"
                    )

                return game_validator.validate_python(data)

            if logger:
                logger.warning(
                    "Demo data was not validated against the Game schema on load. This may cause issues later on."
                )
            else:
                print(
                    "Demo data was not validated against the Game schema on load. This may cause issues later on."
                )
            return data
        except ValidationError as e:
            print(e)
            raise RuntimeError("Schema validation failed during demo load.") from None


class DataManager:
    """Wrapper around an awpy-generated Game object. Function calls replace direct dictionary access, including some error handling."""

    file_path: Path  # Path to the demo file being parsed by awpy
    data: Game

    def __init__(self, file_path: Path, logger=None, do_validate: bool = True):
        self.file_path = file_path
        self.logger = logger
        self.data = _load_game_data(file_path, do_validate, logger)
        self.mappingT = None
        self.mappingCT = None

    def get_match_id(self) -> str | None:
        """Returns the match ID of the Game object, or None if no match ID is found."""
        return self.file_path.stem

    def _get_game_rounds(self) -> list[GameRound]:
        """Returns the list of GameRound objects in the Game object. If there are no game rounds, raises a ValueError."""
        game_rounds = self.data["gameRounds"]
        if game_rounds is None:
            raise ValueError("This game has no round data.")
        return game_rounds

    def get_round_count(self) -> int:
        """Returns the number of rounds in the Game object."""
        return len(self._get_game_rounds())

    def get_game_round(self, round_index: int) -> GameRound:
        """Returns the GameRound object at the given index. If the index is out of bounds, raises a ValueError."""
        rounds = self._get_game_rounds()
        if round_index >= len(rounds):
            raise ValueError(
                f"Round index {round_index} out of bounds (max index is {len(rounds) - 1})"
            )
        return rounds[round_index]

    def get_frame_count(self, round_index: int) -> int:
        """Returns the number of frames in the given round."""
        return len(self._get_frames(round_index))

    def _get_frames(self, round_index: int) -> list[GameFrame]:
        """Returns the list of GameFrame objects in the given round. If there are no frames in the round, raises a ValueError."""
        round_data = self.get_game_round(round_index)
        frames = round_data["frames"]
        if frames is None:
            raise ValueError("No frames found in round")
        return frames

    def get_all_frames(self) -> list[GameFrame]:
        """Returns a list of all GameFrame objects in the Game object."""
        frames = []
        # Iterate through all rounds and collect frames
        # This is done to avoid loading all frames into memory at once, which could be inefficient for large demos
        for round_index in range(self.get_round_count()):
            frames.extend(self._get_frames(round_index))

        return frames

    def get_frame(self, round_index: int, frame_index: int) -> GameFrame:
        """Returns the GameFrame object at the given index in the given round. If the index is out of bounds, raises a ValueError."""
        frames = self._get_frames(round_index)
        if frame_index >= len(frames):
            raise ValueError(
                f"Frame index {frame_index} out of bounds (max index is {len(frames) - 1})"
            )
        return frames[frame_index]

    def get_rounds_frame_count(self) -> list[int]:
        """Returns a list of the number of frames in each round."""
        return [len(self._get_frames(i)) for i in range(self.get_round_count())]

    def get_map_name(self) -> str:
        """Returns the name of the map in the Game object."""
        return self.data["mapName"]

    def get_player_info_lists(
        self, round_index: int, frame_index: int
    ) -> dict[SideType, list[PlayerInfo]]:
        """Returns the list of PlayerInfo objects for both teams in the given round and frame. If no player info is found for a team, raises a ValueError."""
        frame_data = self.get_frame(round_index, frame_index)
        ct_player_info_list = frame_data[SideType.CT.value]["players"]
        if ct_player_info_list is None:
            raise ValueError(
                f"No player info found for team {SideType.CT.value} in round {round_index}, frame {frame_index}"
            )
        t_player_info_list = frame_data[SideType.T.value]["players"]
        if t_player_info_list is None:
            raise ValueError(
                f"No player info found for team {SideType.T.value} in round {round_index}, frame {frame_index}"
            )
        return {SideType.CT: ct_player_info_list, SideType.T: t_player_info_list}

    def get_bomb_info(self, round_index: int, frame_index: int) -> BombInfo:
        """Returns the BombInfo object for the given round and frame. If no bomb info is found, raises a ValueError."""
        frame_data = self.get_frame(round_index, frame_index)
        bomb_info = frame_data["bomb"]
        if bomb_info is None:
            raise ValueError(
                f"No bomb info found in round {round_index}, frame {frame_index}"
            )
        return bomb_info

    # @deprecated
    def get_player_at_frame(
        self, player_index: int, team: SideType, round_index: int, frame_index: int
    ) -> PlayerInfo:
        """DEPCRATED (see below): Returns the PlayerInfo object for the given player in the given team, round, and frame."""
        players = self.get_player_info_lists(round_index, frame_index)[team]
        player = players[
            player_index
        ]  # TODO: NOTE: I don't know if the assumption that players are ordered the same every round is correct. If this is wrong, change how this is done.
        # To be fair, the old way (storing mappings from index to name, mappings which were generated in `get_all_team_routines`) also kind of relied on that assumption in that if untrue, the order of players could change across rounds and that would break the GUI.
        # -> does not work see function get_player_mapped
        return player

    def get_player_idx_mapped(self, player_name: str, team: SideType, frame_data):
        """
        WARNING: This breaks if any player switches sides, disconnects, etc. In that case, you must force
                 re-creation of mappings by using create_player_mapping(..., force_mapping = True)

        TODO: Probably better to switch to SteamID ?

        Args:
            player_name: The player name.
            team: The team to which the player belongs
            frame_data: A frame_data object from which the mapping is created if it does not exist yet.

        Returns:

        """
        if self.mappingT is None or self.mappingCT is None:
            self.create_player_mapping(frame_data)

        mapping = self.mappingT if team == "t" else self.mappingCT
        return mapping[player_name]

    def create_player_mapping(self, frame_data, force_mapping=False):
        # Do not recreate if already exists, as it would change order again and break mapping.
        if self.mappingT is None or force_mapping:
            self.mappingT = dict(
                zip([player["name"] for player in frame_data["t"]["players"]], range(5), strict=False)
            )
        if self.mappingCT is None or force_mapping:
            self.mappingCT = dict(
                zip(
                    [player["name"] for player in frame_data["ct"]["players"]], range(5), strict=False
                )
            )

    def swap_player_mapping(self) -> None:
        """Swaps mappingT and mappingCT when teams switch sides."""
        temp = self.mappingT
        self.mappingT = self.mappingCT
        self.mappingCT = temp

    def is_player_alive(
        self, player_index: int, team: SideType, round_index: int, frame_index: int
    ) -> bool:
        """Returns whether the given player is alive in the given team, round, and frame."""
        player = self.get_player_at_frame(player_index, team, round_index, frame_index)
        return player["isAlive"]

    def get_round_stats(self, round_index: int, frame_index: int) -> RoundStats:
        """Returns a RoundStats object for the given round and frame."""
        round = self.get_game_round(round_index)
        frame = self.get_frame(round_index, frame_index)

        # Round-level stats
        winning_side = SideType.from_str(round["winningSide"])
        round_end_reason = round["roundEndReason"]

        # Frame-level stats
        clock_time = frame["clockTime"]

        # CT-side stats
        opponents_alive = frame["ct"]["alivePlayers"]
        opponent_equipment_value = frame["ct"]["teamEqVal"]

        # T-side stats
        players = [
            Player.from_player_info(player_info)
            for player_info in self.get_player_info_lists(round_index, frame_index)[
                SideType.T
            ]
        ]

        # TODO: Understand why the CT-side stats and the T-side stats we're storing in RoundStats are asymmetric

        return RoundStats(
            players,
            winning_side,
            round_end_reason,
            opponents_alive,
            opponent_equipment_value,
            clock_time,
        )

    def get_player_hp(
        self, player_index: int, team: SideType, round_index: int, frame_index: int
    ) -> int:
        """Returns the HP of the given player in the given team, round, and frame."""
        player = self.get_player_at_frame(player_index, team, round_index, frame_index)
        return player["hp"]

    def _get_players_from_team_from_frame(
        self, frame: GameFrame, team: SideType
    ) -> list[PlayerInfo]:
        """Returns the list of T-side PlayerInfo objects from the given frame object. If no player info is found, raises a ValueError."""
        players = frame[team.value]["players"]
        if players is None:
            raise ValueError(f"No player info found for team {team.value} in frame")
        return players

    def _get_players_from_team(
        self, round_index: int, frame_index: int, team: SideType
    ) -> list[PlayerInfo]:
        """Returns the list of T-side PlayerInfo objects for the given round and frame. If no player info is found, raises a ValueError."""
        frame = self.get_frame(round_index, frame_index)
        return self._get_players_from_team_from_frame(frame, team)

    def get_all_team_routines(
        self, round_index: int, routine_length: FrameCount
    ) -> BothTeamsRoutines:
        """Returns the routines for all players on both teams in the given round in the form of a BothTeams object."""
        frames = self._get_frames(round_index)

        def batch_frames(
            frames: list[GameFrame], chunk_size: int
        ) -> Generator[list[GameFrame], None, None]:
            frame_count = len(frames)
            for index in range(0, frame_count, chunk_size):
                yield frames[index : min(index + chunk_size, frame_count)]

        t_side_routines: dict[str, list[Routine]] = defaultdict(list)
        ct_side_routines: dict[str, list[Routine]] = defaultdict(list)

        for chunk in batch_frames(frames, routine_length):
            t_side_positions: dict[str, list[tuple[float, float]]] = defaultdict(list)
            ct_side_positions: dict[str, list[tuple[float, float]]] = defaultdict(list)
            for frame in chunk:
                for player in self._get_players_from_team_from_frame(frame, SideType.T):
                    t_side_positions[player["name"]].append((player["x"], player["y"]))
                for player in self._get_players_from_team_from_frame(
                    frame, SideType.CT
                ):
                    ct_side_positions[player["name"]].append((player["x"], player["y"]))
            for player_name in t_side_positions:
                # Sometimes we don't have data for every player in a frame - if we have no position data for a player for a whole routine-length, we don't want to create a routine for them
                if len(t_side_positions[player_name]) == 0:
                    continue
                t_side_routines[player_name].append(
                    Routine(
                        player_name,
                        SideType.T,
                        self.get_map_name(),
                        t_side_positions[player_name],
                    )
                )
            for player_name in ct_side_positions:
                # Same as above
                if len(ct_side_positions[player_name]) == 0:
                    continue
                ct_side_routines[player_name].append(
                    Routine(
                        player_name,
                        SideType.CT,
                        self.get_map_name(),
                        ct_side_positions[player_name],
                    )
                )

        t_side = TeamRoutines.from_routines_list(list(t_side_routines.values()))
        ct_side = TeamRoutines.from_routines_list(list(ct_side_routines.values()))

        return BothTeamsRoutines(t_side=t_side, ct_side=ct_side)

    def get_round_start_tick(self, round_index: int) -> int:
        """Returns the tick at which the given round started."""
        round = self.get_game_round(round_index)
        return round["freezeTimeEndTick"]

    def get_round_active_tick_length(self, round_index: int) -> int:
        """Returns the number of ticks between the end of freeze time and the official end of the round."""
        round = self.get_game_round(round_index)
        return round["endOfficialTick"] - round["freezeTimeEndTick"]

    def get_round_events(self, round_index: int) -> RoundActions:
        """Returns a list of events that occurred in the given round in the form of a RoundActions object."""
        round = self.get_game_round(round_index)

        return RoundActions(
            kills=round["kills"] or [],
            damages=round["damages"] or [],
            grenades=round["grenades"] or [],
            bomb_events=round["bombEvents"] or [],
            weapon_fires=round["weaponFires"] or [],
            flashes=round["flashes"] or [],
        )

    def get_team_names(self, round_index: int) -> TeamNames:
        """Returns the names of the two teams in the game."""
        game_round = self.get_game_round(round_index)

        ct_team_name = game_round["ctTeam"]
        if ct_team_name is None:
            raise ValueError("No CT team name found")

        t_team_name = game_round["tTeam"]
        if t_team_name is None:
            raise ValueError("No T team name found")

        return TeamNames(ct_team_name=ct_team_name, t_team_name=t_team_name)

    def get_team_scores(self, round_index: int) -> TeamScore:
        """Returns the scores of the two teams in the game."""
        game_round = self.get_game_round(round_index)

        ct_score = game_round["ctScore"]
        if ct_score is None:
            raise ValueError("No CT score found")

        t_score = game_round["tScore"]
        if t_score is None:
            raise ValueError("No T score found")

        return TeamScore(ct_score=ct_score, t_score=t_score)

    def get_clock_time(self, round_index: int, frame_index: int) -> str:
        """Returns the clock time at the given round and frame."""
        frame = self.get_frame(round_index, frame_index)
        return frame["clockTime"]

    def get_grenade_events(self, round_index: int) -> list[GrenadeAction]:
        """Returns a list of grenade events in the given round."""
        round = self.get_game_round(round_index)
        if round["grenades"] is None:
            raise ValueError("No grenade events found in round")
        return round["grenades"]

    def get_tick_rate(self) -> int:
        """Returns the rate at which the demo was recorded."""
        return self.data["tickRate"]

    def get_parse_rate(self) -> int:
        """Returns the rate at which the demo was parsed."""
        return self.data["parserParameters"]["parseRate"]

    def get_estimated_finish(self, start_time: float, processed_frames: int) -> str:
        """Returns an ETA string based on elapsed time and actual frame progress."""
        total_frames = len(self.get_all_frames())
        if total_frames == 0 or processed_frames == 0:
            return "Calculating ETA..."

        progress = processed_frames / total_frames
        elapsed = time.time() - start_time
        estimated_total_time = elapsed / progress
        remaining_time = estimated_total_time - elapsed
        eta = timedelta(seconds=max(0, int(remaining_time)))
        finish_time = datetime.now() + eta
        return f"Estimated finish: {finish_time.strftime('%H:%M')} (ETA: {str(eta)})"


def get_map_name_from_demo_file_without_parsing(file_path: Path) -> str | None:
    """Returns the map name from a demo file without parsing the whole file. If no map name is found, (i.e. the file is not a valid demo file), returns None.
    Intended to be faster than checking the map name post-parse for use in cases where we are iterating through many demo files and only want to parse a file if it's for a certain map.
    """

    # If it's a valid demo file, there will be a series of characters that looks like this:
    # "mapName": "de_overpass"
    # We can find the map name by looking for this pattern
    pattern = re.compile(r'"mapName": "(\w+)"')

    with open(file_path) as file:
        first_100_chars = file.read(100)
        match = pattern.search(first_100_chars)
        if match:
            return match.group(1)
    return None
