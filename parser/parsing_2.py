import parsing
import awpy.types

from typing import TypedDict

# I used this file to test extracting a new set of data I wasn't extracting before.
# This file doesn't ever really do anything, as I copied-and-pasted this code into cli.py and modified it there to work better.
# Leaving this here for progeny.

class PerformanceScore(TypedDict):
    playerName: str
    didWin: bool
    rawHpDamageDealt: int
    hpDamageDealt: int
    rawArmorDamageDealt: int
    armorDamageDealt: int

class AvailableUtility(TypedDict):
    name: str
    quantity: int

class PlayerInfo(TypedDict):
    playerName: str
    money: int
    equippedWeapon: str
    availableUtilities: list[AvailableUtility]
    positionX: float
    positionY: float
    positionZ: float
    velocityX: float
    velocityY: float
    velocityZ: float

class FrameInfo(TypedDict):
    frameNumber: int
    tick: int
    playerInfo: list[PlayerInfo]

class RoundInfo(TypedDict):
    roundNumber: int
    frameInfo: list[FrameInfo]
    performanceScores: list[PerformanceScore]

class WritableRoundRow(TypedDict):
    roundNumber: int
    frameNumber: int
    tick: int
    playerName: str 
    money: int
    equippedWeapon: str
    positionX: float
    positionY: float
    positionZ: float
    velocityX: float
    velocityY: float
    velocityZ: float
    decoyGrenadeCount: int
    fireGrenadeCount: int
    flashGrenadeCount: int
    heGrenadeCount: int
    smokeGrenadeCount: int
    didWin: bool
    rawHpDamageDealtInRound: int
    hpDamageDealtInRound: int
    rawArmorDamageDealtInRound: int
    armorDamageDealtInRound: int

def parse(game_data: awpy.types.Game) -> list[list[WritableRoundRow]]:
    '''
    To analyze the game play data better we need some additional data from the CS demos. Here are the changes that (hopefully) can be implemented:
    - Keystrokes: do you think it's possible to get the information on which buttons they press/hold at what time?
    - the current time interval is 1 sec. if I'm not mistaken. Can we get three different time intervals in addition? We want to check if that changes the level of abstraction and maybe makes it easier to see patterns/analyse the data. Preferably 5, 10, and 15 sec. intervals.
    - the status on game economics: Which player has how much money.
    - available utilities: how many/which utilities are left this round for each players?
    - Split the data for per round. Maybe one Excel file per round?
    - the movement speed of each player each interval. What's the maximum movement speed (running with a knife vs. crouching with a weapon)?
    Do you think it's possible to implement those things? If so, when do you got time to work on it?
    - performance scores per round (win-lose, damage dealt) 
    '''

    all_round_info: dict[int, dict] = {}

    for game_round in game_data["gameRounds"]:
        round_info: RoundInfo = {
            "roundNumber": game_round["roundNum"],
            "frameInfo": [],
            "performanceScores": [],
        }

        ct_side_players = game_round["ctSide"]["players"]
        t_side_players = game_round["tSide"]["players"]
        ct_side_player_names = [player["playerName"] for player in ct_side_players]
        t_side_player_names = [player["playerName"] for player in t_side_players]
        all_players: list[awpy.types.Players] = ct_side_players + t_side_players
        winning_side = game_round["winningSide"]

        for player in all_players:
            performance_info: PerformanceScore = {
                "playerName": "",
                "didWin": False,
                "rawHpDamageDealt": 0,
                "hpDamageDealt": 0,
                "rawArmorDamageDealt": 0,
                "armorDamageDealt": 0,
            }

            player_name = player["playerName"]
            performance_info["playerName"] = player_name

            if winning_side == "CT":
                if player_name in ct_side_player_names:
                    performance_info["didWin"] = True
            else:
                if player_name in t_side_player_names:
                    performance_info["didWin"] = True

            for damage in game_round["damages"]:
                if damage["attackerName"] == player_name:
                    performance_info["rawHpDamageDealt"] += damage["hpDamage"]
                    performance_info["hpDamageDealt"] += damage["hpDamageTaken"]
                    performance_info["rawArmorDamageDealt"] += damage["armorDamage"]
                    performance_info["armorDamageDealt"] += damage["armorDamageTaken"]

            round_info["performanceScores"].append(performance_info)
            

        for frame_index, frame in enumerate(game_round["frames"]):
            frame_info: FrameInfo = {
                "frameNumber": frame_index,
                "tick": frame["tick"],
                "playerInfo": [],
            }
            
            ct_info = frame["ct"]
            t_info = frame["t"]

            ct_players = ct_info["players"]
            t_players = t_info["players"]
            all_player_info: list[awpy.types.PlayerInfo] = ct_players + t_players

            for player_info in all_player_info:
                player_data: PlayerInfo = {
                    "playerName": player_info["name"],
                    "money": player_info["cash"],
                    "availableUtilities": [],
                    "velocityX": player_info["velocityX"],
                    "velocityY": player_info["velocityY"],
                    "velocityZ": player_info["velocityZ"],
                }

                current_utility_count = 0
                for utility_type in ["heGrenade", "fireGrenade", "smokeGrenade", "flashGrenade"]:
                    available_utility: AvailableUtility = {
                        "name": utility_type,
                        "quantity": player_info[utility_type],
                    }
                    current_utility_count += player_info[utility_type]
                    
                    player_data["availableUtilities"].append(available_utility)
                # Because decoy grenades don't seem to be counted, assuming any utility items that aren't accounted for are decoy grenades
                if current_utility_count != player_info["totalUtility"]:
                    available_decoy: AvailableUtility = {
                        "name": "decoyGrenade",
                        "quantity": player_info["totalUtility"] - current_utility_count,
                    }
                    player_data["availableUtilities"].append(available_decoy)

                frame_info["playerInfo"].append(player_data)

        all_round_info.append(round_info)

    writable_round_rows: list[list[WritableRoundRow]] = []
    
    for round_info in all_round_info:
        round_rows: list[WritableRoundRow] = []
        for frame_info in round_info["frameInfo"]:
            for player_info in frame_info["playerInfo"]:

                performance_score_info = [score_dict for score_dict in round_info["performanceScores"] if score_dict["playerName"] == player_info["playerName"]][0]

                round_row: WritableRoundRow = {
                    "roundNumber": round_info["roundNumber"], 
                    "frameNumber": frame_info["frameNumber"], 
                    "tick": frame_info["tick"], 
                    "playerName": player_info["playerName"],
                    "money": player_info["money"], 
                    "velocityX": player_info["velocityX"], 
                    "velocityY": player_info["velocityY"], 
                    "velocityZ": player_info["velocityZ"], 
                    "decoyGrenadeCount": sum([grenade.quantity for grenade in player_info["availableUtilities"] if grenade["name"] == "decoyGrenade"]), 
                    "fireGrenadeCount": sum([grenade.quantity for grenade in player_info["availableUtilities"] if grenade["name"] == "fireGrenade"]), 
                    "flashGrenadeCount": sum([grenade.quantity for grenade in player_info["availableUtilities"] if grenade["name"] == "flashGrenade"]), 
                    "heGrenadeCount": sum([grenade.quantity for grenade in player_info["availableUtilities"] if grenade["name"] == "heGrenade"]), 
                    "smokeGrenadeCount": sum([grenade.quantity for grenade in player_info["availableUtilities"] if grenade["name"] == "smokeGrenade"]), 
                    "didWin": performance_score_info["didWin"], 
                    "rawHpDamageDealtInRound": performance_score_info["rawHpDamageDealt"], 
                    "hpDamageDealtInRound": performance_score_info["hpDamageDealt"], 
                    "rawArmorDamageDealtInRound": performance_score_info["rawArmorDamageDealt"], 
                    "armorDamageDealtInRound": performance_score_info["armorDamageDealt"]
                }

                round_rows.append(round_row)
        writable_round_rows.append(round_rows)

    return writable_round_rows

def main():
    dust_demo_location = "./demos/cloud9-vs-outsiders-m1-dust2.dem"
    parse(dust_demo_location)

if __name__ == "__main__":
    main()