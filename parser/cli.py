import parsing
import models
import timelining
import plotting
import mathing
from tqdm import tqdm
import networkx as nx
import tkinter as tk
from tkinter import filedialog
import os
import csv
from dataclasses import fields
import shutil
from parsing_2 import WritableRoundRow, RoundInfo, PlayerInfo, AvailableUtility, PerformanceScore, FrameInfo
import awpy.types

def extract_demo_data() -> None:
    """
    Run the main 'extract data' routine in console mode
    """

    root = tk.Tk()
    # To open file dialog in a new window on top of everything else instead of behind everything else
    root.wm_attributes('-topmost', 1)
    root.withdraw()

    print("Select the .dem file from which you would like to extract the data (see new window):")
    input_file_path = filedialog.askopenfilename(title="Open a .dem file",filetypes=[("demo files", "*.dem")])
    if input_file_path == "":
        print("No file selected, cancelling.")
        return
    print("Extracting data from file: " + input_file_path)

    print("Select the directory in which you would like to save the .csv and image files (see new window):")
    output_directory = filedialog.askdirectory(initialdir=os.getcwd(), title="Choose where you want the .csv and .gif files to be saved:")
    if output_directory == "":
        print("No directory selected, cancelling.")
        return
    print("Saving data to directory: " + output_directory)

    if os.path.isdir(output_directory) is False:
        print("Output directory does not exist. Creating directory.")
        os.mkdir(output_directory)

    print("Beginning data extraction...")
    print(f"Loading demo file at {input_file_path}, please wait...")
    parsed_demo_data = parsing.parse_demo_file(input_file_path)
    demo: models.Demo = models.deserialize_demo_data(parsed_demo_data)
    print("Loaded demo file.")
    print("Creating event timeline.")
    timeline: timelining.Timeline = timelining.create_timeline(demo)
    print("Demo analyzed, timeline created.")

    events_file_name: str = f"{output_directory}/events.csv"
    print(f"Saving event timeline to {events_file_name}")
    with open(events_file_name, "w") as file:
        writer = csv.writer(file)
        all_fields: list[str] = []
        for event in timeline.events:
            all_fields.extend([field.name for field in fields(event)])
        unique_fields = list(dict.fromkeys(all_fields))
        writer.writerow([field for field in unique_fields])
        for event in timeline.events:
            writer.writerow([getattr(event, field, None) for field in unique_fields])
    print("Event timeline saved.")

    event_descriptions_file_name: str = f"{output_directory}/event_descriptions.csv"
    print(f"Saving event descriptions to {event_descriptions_file_name}")
    with open(event_descriptions_file_name, "w") as file:
        writer = csv.writer(file)
        writer.writerow(["tick", "name", "description"])
        for event in timeline.events:
            writer.writerow([event.tick, event.__class__.__name__, str(event)])
    print("Event descriptions saved.")

    print("Calculating frame-specific data and saving frame images for every round in the game.")
    print("This might take a while. Go do something else while you wait!")
    rounds_folder: str = f"{output_directory}/round_visualizations"
    if os.path.isdir(rounds_folder) is False:
        print("Round visualizations folder does not exist. Creating folder.")
        os.mkdir(rounds_folder)
    print(f"Saving to {rounds_folder}")
    # Moved this dictionary out here because now it will track controlled_area_sizes for the whole game instead of one round
    controlled_area_sizes: dict[int, dict[str, float]] = {}
    for round_index, round in enumerate(demo.game_rounds):
        round_number = round_index + 1
        vision_graphs: list[nx.Graph] = []
        vision_traces: list[dict[int, mathing.VisionTraceResults]] = []
        with tqdm(total=len(round.frames), desc=f"Calculating frame vision information for round {round_index+1}/{len(demo.game_rounds)}: ") as progress_bar:
            for frame in round.frames:
                vision_graph: nx.Graph
                trace_results: dict[int, mathing.VisionTraceResults]
                vision_graph, trace_results = mathing.calculate_vision_graph(frame=frame, map_name=demo.map_name)
                vision_graph = mathing.grow_controlled_areas(frame=frame, map_graph=vision_graph)
                controlled_area_sizes[frame.tick] = mathing.calculate_controlled_area_sizes(map_graph=vision_graph, map_name=demo.map_name)
                vision_graphs.append(vision_graph)
                vision_traces.append(trace_results)
                progress_bar.update()
        folder_name = f"{rounds_folder}/round_{round_number}"
        if os.path.isdir(folder_name):
            print(f"{folder_name} already exists. Emptying it's contents.")
            shutil.rmtree(f"{folder_name}/")
        os.mkdir(folder_name)
        plotting.plot_round(
            image_directory=folder_name, 
            round_number=round_number,
            round=round, 
            vision_graphs=vision_graphs,
            vision_traces=vision_traces,
            map_name=demo.map_name,
        )
        print("Saved round images.")

        area_controlled_file_name: str = f"{output_directory}/area_controlled.csv"
        print(f"Saving area controlled data to {area_controlled_file_name}")
        with open(output_directory + "/area_controlled.csv", "w") as file:
            writer = csv.writer(file)
            writer.writerow(["tick", "CT", "T"])
            for tick, controlled_area_size_dict in controlled_area_sizes.items():
                writer.writerow([tick, controlled_area_size_dict["CT"], controlled_area_size_dict["T"]])
        print("Area controlled data saved.")

    print(f"Done saving the game! Check the {output_directory} folder for the output files.")


def parsing_2() -> None:
    """
    Run the main 'extract data' routine in console mode
    """

    root = tk.Tk()
    # To open file dialog in a new window on top of everything else instead of behind everything else
    root.wm_attributes('-topmost', 1)
    root.withdraw()

    print("Select the .dem file from which you would like to extract the data (see new window):")
    input_file_path = filedialog.askopenfilename(title="Open a .dem file",filetypes=[("demo files", "*.dem")])
    if input_file_path == "":
        print("No file selected, cancelling.")
        return
    print("Extracting data from file: " + input_file_path)

    print("Select the directory in which you would like to save the .csv files (see new window):")
    output_directory = filedialog.askdirectory(initialdir=os.getcwd(), title="Choose where you want the .csv and .gif files to be saved:")
    if output_directory == "":
        print("No directory selected, cancelling.")
        return
    print("Saving data to directory: " + output_directory)

    if os.path.isdir(output_directory) is False:
        print("Output directory does not exist. Creating directory.")
        os.mkdir(output_directory)

    print("Beginning data extraction...")
    print(f"Loading demo file at {input_file_path}, please wait...")
    game_data = parsing.parse_demo_file(input_file_path)
    print("Loaded demo file.")
    print("Compartmentalizing round-specific information.")

    all_round_info: list[RoundInfo] = []

    for round_index, game_round in enumerate(tqdm(game_data["gameRounds"])):

        tqdm.write(f"Processing round {round_index}")

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
                    "equippedWeapon": player_info["activeWeapon"],
                    "availableUtilities": [],
                    "positionX": player_info["x"],
                    "positionY": player_info["y"],
                    "positionZ": player_info["z"],
                    "velocityX": player_info["velocityX"],
                    "velocityY": player_info["velocityY"],
                    "velocityZ": player_info["velocityZ"],
                }

                current_utility_count = 0
                for utility_type in ["heGrenades", "fireGrenades", "smokeGrenades", "flashGrenades"]:
                    available_utility: AvailableUtility = {
                        "name": utility_type,
                        "quantity": player_info[utility_type],
                    }
                    current_utility_count += player_info[utility_type]
                    
                    player_data["availableUtilities"].append(available_utility)

                # Manually check for decoy grenades because AWPY doesn't provide that information
                if player_info["inventory"] is not None:
                    for weapon in player_info["inventory"]:
                        if weapon["weaponName"] == "Decoy Grenade":
                            available_utility: AvailableUtility = {
                                "name": "decoyGrenades",
                                "quantity": weapon["ammoInMagazine"],
                            }
                            player_data["availableUtilities"].append(available_utility)

                frame_info["playerInfo"].append(player_data)

            round_info["frameInfo"].append(frame_info)

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
                    "equippedWeapon": player_info["equippedWeapon"], 
                    "positionX": player_info["positionX"],
                    "positionY": player_info["positionY"],
                    "positionZ": player_info["positionZ"],
                    "velocityX": player_info["velocityX"], 
                    "velocityY": player_info["velocityY"], 
                    "velocityZ": player_info["velocityZ"], 
                    "decoyGrenadeCount": sum([grenade["quantity"] for grenade in player_info["availableUtilities"] if grenade["name"] == "decoyGrenades"]), 
                    "fireGrenadeCount": sum([grenade["quantity"] for grenade in player_info["availableUtilities"] if grenade["name"] == "fireGrenades"]), 
                    "flashGrenadeCount": sum([grenade["quantity"] for grenade in player_info["availableUtilities"] if grenade["name"] == "flashGrenades"]), 
                    "heGrenadeCount": sum([grenade["quantity"] for grenade in player_info["availableUtilities"] if grenade["name"] == "heGrenades"]), 
                    "smokeGrenadeCount": sum([grenade["quantity"] for grenade in player_info["availableUtilities"] if grenade["name"] == "smokeGrenades"]), 
                    "didWin": performance_score_info["didWin"], 
                    "rawHpDamageDealtInRound": performance_score_info["rawHpDamageDealt"], 
                    "hpDamageDealtInRound": performance_score_info["hpDamageDealt"], 
                    "rawArmorDamageDealtInRound": performance_score_info["rawArmorDamageDealt"], 
                    "armorDamageDealtInRound": performance_score_info["armorDamageDealt"]
                }

                round_rows.append(round_row)
        writable_round_rows.append(round_rows)  

    print("Writing round-specific information to csv files.")

    for round_index, round_rows in enumerate(tqdm(writable_round_rows)):
        csv_file_name: str = f"{output_directory}/round_{round_index}.csv"
        with open(csv_file_name, "w", newline="") as file:
            writer = csv.writer(file)
            all_fields: list[str] = [key for key in list(WritableRoundRow.__annotations__.keys())]
            writer.writerow(all_fields)
            for row in round_rows:
                writer.writerow([row[key] for key in row])
        tqdm.write(f"Saved csv file for round {round_index} at {csv_file_name}")

    print("Writing round-specific action information to csv files.")

    # Per round, read kills, damages, bombEvents, startTick, endTick, endOfficialTick (and initial player money if possible)
    for round_index, game_round in enumerate(tqdm(game_data["gameRounds"])):
        kills: list[awpy.types.KillAction] = game_round["kills"]
        damages: list[awpy.types.DamageAction] = game_round["damages"]
        bomb_events: list[awpy.types.BombAction] = game_round["bombEvents"]
        tick_info = {
            "startTick": game_round["startTick"],
            "endTick": game_round["endTick"],
            "endOfficialTick": game_round["endOfficialTick"]
        }

        info_to_write: list = [*kills, *damages, *bomb_events, tick_info]
        all_fields: list = ["tick", "actionType"]
        for obj in info_to_write:
            keys = sorted(obj.keys())
            for key in keys:
                if key not in all_fields:
                    all_fields.append(key)

        csv_file_name: str = f"{output_directory}/round_{round_index}_actions.csv"
        with open(csv_file_name, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=all_fields)

            # Write the header row to the file
            writer.writeheader()

            # Loop over the list of mixed objects and write each row to the CSV file
            for obj in kills:
                default_dict = {field: '' for field in writer.fieldnames}
                default_dict["actionType"] = "kill"
                default_dict.update(obj)
                writer.writerow(default_dict)

            for obj in damages:
                default_dict = {field: '' for field in writer.fieldnames}
                default_dict["actionType"] = "damage"
                default_dict.update(obj)
                writer.writerow(default_dict)
            
            for obj in bomb_events:
                default_dict = {field: '' for field in writer.fieldnames}
                default_dict["actionType"] = "bombEvent"
                default_dict.update(obj)
                writer.writerow(default_dict)

            for obj in [tick_info]:
                default_dict = {field: '' for field in writer.fieldnames}
                default_dict["actionType"] = "roundTickInfo"
                default_dict.update(obj)
                writer.writerow(default_dict)

    print(f"Done writing csv files. Check the {output_directory} folder for the output files.")
    
def main() -> None:
    """
    Launch CLI version of the program
    """
    print("Welcome to the CS:GO Demo File Player Data Extractor!")
    do_quit: bool = False
    while do_quit is False:
        print("Select an option:")
        print("""1. Extract data from a .dem file, creating .csv files for game events and team area controlled, 
        as well as .gifs for visualizing the area controlled by each team.""")
        print("""2. Extract data from a .dem file, creating a .csv file per round of the game that contains 
        economy, utility, player movement, and player performance data.""")
        print("Q. Quit")
        user_input = input("Enter your choice: ").upper()
        if user_input not in ["1", "2", "Q"]:
            print("Invalid input. Please try again.")
            continue
        if user_input == "1":
            extract_demo_data()
        elif user_input == "2":
            parsing_2()
        elif user_input == "Q":
            do_quit = True
            input("Closing. Press ENTER to continue.")
            return

if __name__ == "__main__":
    main()