import os
import shutil
import imageio
import matplotlib
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.pyplot as plt
from awpy.visualization import plot
from awpy.data import NAV
import networkx as nx
from tqdm import tqdm
import models
import mathing

CT_COLOR: str = "xkcd:azure"
T_COLOR: str = "xkcd:orange"
BOMB_COLOR: str = "yellow"
CT_TILE_COLOR: str = "xkcd:lightblue"
T_TILE_COLOR: str = "darkorange"
SMOKE_COLOR: str = "grey"
FIRE_COLOR: str = "red"
DEFAULT_COLOR: str = "black"

def plot_navigation_mesh(map_name: str, map_type: str, dark: bool) -> tuple[Figure, Axes]:
    """
    Plots the map's navigation mesh
    """

    f: Figure
    ax: Axes

    f, ax = plot.plot_map(map_name = map_name, map_type = map_type, dark = dark)

    for a in NAV[map_name]:
        tile = NAV[map_name][a]
        x_se = plot.position_transform(map_name, tile["southEastX"], "x")
        x_nw = plot.position_transform(map_name, tile["northWestX"], "x")
        y_se = plot.position_transform(map_name, tile["southEastY"], "y")
        y_nw = plot.position_transform(map_name, tile["northWestY"], "y")
        width = (x_se - x_nw)
        height = (y_nw - y_se)
        southwest_x = x_nw
        southwest_y = y_se
        rect = matplotlib.patches.Rectangle((southwest_x,southwest_y), width, height, linewidth=0.2, edgecolor="yellow", facecolor="None")
        ax.add_patch(rect)

    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    return f, ax

def plot_rounds(demo_file_data, output_file_directory: str) -> None:
    """
    Given a parsed demo file, plot all rounds of the demo and save it to a file
    Output file name shouldn't contain extensions
    """
    total_rounds = len(demo_file_data["gameRounds"])
    for index, round in enumerate(demo_file_data["gameRounds"]):
        # TODO: Make sure that the output is sent to the right place
        print(f"Creating .gif for round {index}/{total_rounds}:")
        plot_round(f"{output_file_directory}/round{index}.gif", round["frames"], map_name=demo_file_data["mapName"])

def plot_round(
    image_directory: str, 
    round_number: int,
    round: models.Round,
    vision_graphs: list[nx.Graph],
    vision_traces: list[dict[int, mathing.VisionTraceResults]],
    map_name: str, 
    map_type: str = "simpleradar", 
    dark: bool = False, 
    show_tiles: bool = True,
    gif_frame_rate: int = 2
    ) -> bool:
    """Plots a round and saves as a .gif. CTs are blue, Ts are orange, and the bomb is an octagon. Only use untransformed coordinates.

    Args:
        folder_name (string): folder name to save the frame images and the round gif
        round (list): the round to plot
        map_name (string): Map to search
        map_type (string): "original" or "simpleradar"
        dark (boolean): Only for use with map_type="simpleradar". Indicates if you want to use the SimpleRadar dark map type
        show_tiles: (boolean): The round images will have the outlines of each map tile displayed
        gif_frame_rate (int): The frames per second at which the GIF will play

    """
    image_files: list[str] = []
    frames = round.frames
    grenade_throwers: dict[tuple[float, float, float], str] = {
        (g.grenade_x, g.grenade_y, g.grenade_z): g.thrower_side for g in round.grenades
    }
    with tqdm(total=len(frames), desc = "Drawing frames: ") as progress_bar:
        for index, frame in enumerate(frames):
            vision_graph = vision_graphs[index]
            vision_trace_results = vision_traces[index]
            f, a = plot_frame(
                frame=frame, 
                grenade_throwers=grenade_throwers, 
                map_graph=vision_graph,
                vision_trace_results=vision_trace_results,
                map_name=map_name, 
                map_type=map_type, 
                dark=dark, 
                show_tiles=show_tiles
            )
            image_files.append(f"{image_directory}/frame_{index+1}.png")
            f.tight_layout(pad=0)
            f.savefig(image_files[-1], dpi=300, bbox_inches="tight", pad_inches=0)
            plt.close()
            progress_bar.update()
    images = []
    for file in image_files:
        images.append(imageio.imread(file))
    imageio.mimsave(f"{image_directory}/round_{round_number}.gif", images, fps=gif_frame_rate)
    return True

def plot_frame(
    frame: models.Frame, 
    grenade_throwers: dict[int, str], 
    map_graph: nx.Graph, 
    vision_trace_results: dict[int, mathing.VisionTraceResults],
    map_name: str, 
    map_type: str, 
    dark: bool, 
    show_tiles: bool = True
    ) -> tuple[Figure, Axes]:
    """
    Plots a frame and returns the figure, axes, and the map graph (containing area controlled information).
    CTs are blue, Ts are orange, and the bomb is an octagon.
    """
    if show_tiles is True:
        f, a = plot_navigation_mesh(map_name, map_type, dark)
    else:
        f, a = plot.plot_map(map_name, map_type, dark)

    x_transform = lambda x: plot.position_transform(map_name, x, "x")
    y_transform = lambda y: plot.position_transform(map_name, y, "y")

    if frame.bomb is not None:
        bomb_x = x_transform(frame.bomb.x)
        bomb_y = y_transform(frame.bomb.y)
        a.scatter(x=bomb_x, y=bomb_y, c=BOMB_COLOR, marker="8")

    team: models.TeamFrameState
    color: str
    for team, color in [(frame.ct, CT_COLOR), (frame.t, T_COLOR)]:
        player_group: list[models.PlayerFrameState] = team.players
        for index, player in enumerate(player_group):

            player_x: float = x_transform(player.x)
            player_y: float = y_transform(player.y)

            if player.hp <= 0:
                a.scatter(x=player_x, y=player_y, c=color, marker="x")
                continue

            a.scatter(x=player_x, y=player_y, c=color, marker=".")

            # Draw lines between this player and other alive players
            for player2 in [p for p in player_group[index:] if p.hp > 0]:
                player2_x = x_transform(player2.x)
                player2_y = y_transform(player2.y)
                x_values = [player_x, player2_x]
                y_values = [player_y, player2_y]
                a.plot(x_values, y_values, c=color, linestyle="dotted", linewidth="0.7")

            aim_end_point = vision_trace_results[player.steam_id].end_points[0]
            # Draw a line to where the player is aiming
            a.scatter(x=x_transform(aim_end_point[0]), y=y_transform(aim_end_point[1]), c=color, marker="2")
            a.plot([player_x, x_transform(aim_end_point[0])], [player_y, y_transform(aim_end_point[1])], c=color, linestyle="solid", linewidth=0.85)

            # Draw lines for every view vector cast
            for end_point in vision_trace_results[player.steam_id].end_points[1:]:
                view_vector_end_point_x = x_transform(end_point[0])
                view_vector_end_point_y = y_transform(end_point[1])
                x_values = [player_x, view_vector_end_point_x]
                y_values = [player_y, view_vector_end_point_y]
                # a.scatter(x=end_point[0], y=end_point[1], c=color, marker="2")
                a.plot(x_values, y_values, c=color, linestyle="dotted", linewidth="0.4", alpha=0.2)

    # Color tiles!
    for node in map_graph.nodes(data=True):
        node_data: dict = node[1]
        controlling_side = node_data.get("controlling_side", None)
        if controlling_side is None:
            continue
        elif controlling_side == "CT":
            color = CT_TILE_COLOR
        elif controlling_side == "T":
            color = T_TILE_COLOR

        area_id: int = node_data["areaID"]
        tile = NAV[map_name][area_id]

        x_se = x_transform(tile["southEastX"])
        x_nw = x_transform(tile["northWestX"])
        y_se = y_transform(tile["southEastY"])
        y_nw = y_transform(tile["northWestY"])
        width = (x_se - x_nw)
        height = (y_nw - y_se)
        southwest_x = x_nw
        southwest_y = y_se   

        rect = matplotlib.patches.Rectangle((southwest_x,southwest_y), width, height, linewidth=0.4, edgecolor=color, facecolor=color, alpha=0.2)
        a.add_patch(rect)

    # TODO: Resize markers to match how big they are in game if necessary

    marker_size: int = 400

    def get_thrower_of_closest_grenade(x: float, y: float, z: float) -> str:
        """
        Given a grenade's x, y, z coordinates, find the thrower of the closest grenade
        """
        closest_grenade_id = min(grenade_throwers, key=lambda g: (g[0] - x)**2 + (g[1] - y)**2 + (g[2] - z)**2)
        return grenade_throwers[closest_grenade_id]

    for smoke in frame.smokes:
        smoke_x: float = plot.position_transform(map_name, smoke.x, "x")
        smoke_y: float = plot.position_transform(map_name, smoke.y, "y")
        owner = get_thrower_of_closest_grenade(smoke.x, smoke.y, smoke.z)
        outline_color = CT_COLOR if owner == "CT" else T_COLOR if owner == "T" else SMOKE_COLOR
        a.scatter(x=smoke_x, y=smoke_y, c=SMOKE_COLOR, marker=".", edgecolors=outline_color, s=marker_size,)

    for fire in frame.fires:
        fire_x: float = plot.position_transform(map_name, fire.x, "x")
        fire_y: float = plot.position_transform(map_name, fire.y, "y")
        owner = get_thrower_of_closest_grenade(fire.x, fire.y, fire.z)
        outline_color = CT_COLOR if owner == "CT" else T_COLOR if owner == "T" else FIRE_COLOR
        a.scatter(x=fire_x, y=fire_y, c=FIRE_COLOR, marker=".", edgecolors=outline_color, s=marker_size,)

    return f, a