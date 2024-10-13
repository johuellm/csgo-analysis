from awpy.analytics import nav
from awpy.data import NAV, NAV_GRAPHS
import networkx as nx
import models
import numpy as np
from dataclasses import dataclass, field

@dataclass
class VisionTraceResults:
    """
    Contains information about the results of a vision ray cast.
    The first angle in angled_traced is a straight line forward from where the player is looking.
    (and the first value in end_points is the first wall the player's vision ray encounters.)
    """
    angles_traced: list[float] = field(default_factory=list) # In degrees
    end_points: list[tuple[float, float, float]] = field(default_factory=list)
    visible_area_ids: list[int] = field(default_factory=list)

def trace_vision(player: models.PlayerFrameState, frame: models.Frame, map_name: str, fov: int = 90, ray_count: int = 30, step_size: int = 20) -> VisionTraceResults:
    """
    Given a player position and view angle, trace multiple lines in their vision cone. Returns a VisionTraceResults object.
    fov is (in degrees) how large the "vision cone" is.
    ray_count is the number of lines to draw, the more lines, the more accurate the results but the slower the function.
    step_size is how far along each line we check to see if the line has collided with something - 
        the more steps, the more accurate the results but the slower the function.
    """
    trace_results: VisionTraceResults = VisionTraceResults()

    visible_area_ids: set[int] = set()

    player_area_id: int = nav.find_closest_area(map_name, (player.x, player.y, player.z)).get("areaId", None)
    if player_area_id is None:
        return list(visible_area_ids)
    visible_area_ids.add(player_area_id)

    angles_to_trace: list[float] = [player.view_x]
    angles_to_trace.extend([player.view_x + i for i in range(int(-fov/2), int(fov/2 + 1), int(fov/ray_count))])

    trace_results.angles_traced = angles_to_trace

    angles_to_trace = np.deg2rad(angles_to_trace)

    def is_point_in_smoke(x: float, y: float, z: float) -> bool:
        """
        Given a point, returns if it is in a smoke or not
        """
        SMOKE_RADIUS: int = 144 # Taken from CS:GO wiki
        for smoke in frame.smokes:
            x_bounds: list[float] = [smoke.x - SMOKE_RADIUS, smoke.x + SMOKE_RADIUS]
            y_bounds: list[float] = [smoke.y - SMOKE_RADIUS, smoke.y + SMOKE_RADIUS]
            z_bounds: list[float] = [smoke.z - SMOKE_RADIUS, smoke.z + SMOKE_RADIUS]
            if all([x_bounds[0] <= x <= x_bounds[1], y_bounds[0] <= y <= y_bounds[1], z_bounds[0] <= z <= z_bounds[1]]):
                return True

        return False

    for angle in angles_to_trace:
        dx: float = np.cos(angle)*step_size
        dy: float = np.sin(angle)*step_size
        next_point: tuple[float, float, float] = (player.x, player.y, player.z)
        do_end_raycast: bool = False
        iteration_count: int = 0
        nearest_area_id: int = player_area_id
        while do_end_raycast is False:
            iteration_count += 1
            do_end_raycast = True
            if is_point_in_smoke(next_point[0], next_point[1], next_point[2]) is False:
                # TODO: If we can find a way to intelligently decrease the amount of area_ids we test, this will be faster.
                # If we are not in an area then we have gone out of bounds (we probably are in a wall or something so this is our "collision")
                if nav.point_in_area(map_name, nearest_area_id, next_point) is True:
                    do_end_raycast = False
                    next_point = (player.x + iteration_count*dx, player.y + iteration_count*dy, player.z)
                else:
                    for area_id in NAV[map_name].keys():
                        if nav.point_in_area(map_name, area_id, next_point) is True:
                            nearest_area_id = area_id
                            do_end_raycast = False
                            next_point = (player.x + iteration_count*dx, player.y + iteration_count*dy, player.z)
                            visible_area_ids.add(area_id)

        trace_results.end_points.append(next_point)
    
    trace_results.visible_area_ids = list(visible_area_ids)

    return trace_results

def calculate_vision_graph(frame: models.Frame, map_name: str) -> tuple[nx.Graph, dict]:
    """
    Returns a map graph with each node containing information about who is viewing it
    Also returns a map of player steam_id to their entire VisionTraceResults object
    """
    map_graph: nx.Graph = nx.Graph(NAV_GRAPHS[map_name])
    vision_trace_results: dict[int, VisionTraceResults] = {}

    for node in map_graph.nodes(data=True):
        node_data: dict = node[1]
        previous_covered_by_set: set[int] = node_data.get("covered_by", None) or set()
        node_data["covered_by"] = set()
        node_data["previously_covered_by"] = previous_covered_by_set

    for player in [p for p in frame.ct.players + frame.t.players if p.hp > 0]:
        trace_results: VisionTraceResults = trace_vision(player=player, frame=frame, map_name=map_name)
        vision_trace_results[player.steam_id] = trace_results

        for visible_area_id in trace_results.visible_area_ids:
            for node in map_graph.nodes(data=True):
                area_id: int = node[0]
                if visible_area_id == area_id:
                    node_data: dict = node[1]
                    node_data["covered_by"].add(player.steam_id)

    return (map_graph, vision_trace_results)

def grow_controlled_areas(frame: models.Frame, map_graph: nx.Graph) -> nx.Graph:
    """
    TODO: Iteratively grow zones of control for each team 
    (after setting each player's current position as in their control (if there are no enemies in the tile))

    TODO: Figure out controlled area growth rules.
    Idea: maybe if a tile has a neighbor that is a color, and it has no path to the opposite color, make it that color.
    Idea: if a tile is viewed by a side, mark it as viewed by that player.
      if that tile is then viewed by a player from the enemy team, mark it as viewed by that player.
      if a player dies, mark every tile that they were viewing as no longer viewed
      
    each tile has a "covered_by" attribute, which is a list of players that are viewing it.

    initialize graph with the base positions of each team
    (where they are standing)
    """

    alive_ct_player_ids = [p.steam_id for p in frame.ct.players if p.hp > 0]
    alive_t_player_ids = [p.steam_id for p in frame.t.players if p.hp > 0]

    for node in map_graph.nodes(data=True):
        node_data: dict = node[1]
        node_data["controlling_side"] = None
        ct_count = 0
        t_count = 0
        # Commenting this out to disable vision persisting across frames
        # If this tile hasn't been updated this frame (i.e. viewed) then just use the information from last frame
        # if len(node_data["covered_by"]) == 0:
        #     node_data["covered_by"] = node_data["previously_covered_by"]
        covered_by_set: set[int] = node_data["covered_by"]
        for player in covered_by_set:
            if player in alive_ct_player_ids:
                ct_count += 1
            elif player in alive_t_player_ids:
                t_count += 1
        if ct_count > t_count:
            node_data["controlling_side"] = "CT"
        elif t_count > ct_count:
            node_data["controlling_side"] = "T"
        elif ct_count == t_count:
            node_data["controlling_side"] = None
    
    # # Spread the zones of control as far as they should
    # # TODO: This is not super great (it's wrong a lot)
    # graph_did_change: bool = True
    # graph_did_change = False # TODO: Re-enable this
    # while graph_did_change:
    #     graph_did_change = False
    #     for node in map_graph.nodes(data=True):
    #         area_id: int = node[0]
    #         node_data: dict = node[1]
    #         ct_zone_neighbor_count: int = 0
    #         t_zone_neighbor_count: int = 0
    #         if node_data["controlling_side"] is not None:
    #             continue
    #         for neighbor in map_graph.neighbors(area_id):
    #             neighbor_data: dict = map_graph.nodes[neighbor]
    #             if neighbor_data["controlling_side"] == "CT":
    #                 ct_zone_neighbor_count += 1
    #             elif neighbor_data["controlling_side"] == "T":
    #                 t_zone_neighbor_count += 1
    #         if ct_zone_neighbor_count >= 2 and t_zone_neighbor_count == 0:
    #             node_data["controlling_side"] = "CT"
    #             ct_covered_area_ids.add(node_data["areaID"])
    #             # print(f"Zone {node_data['areaID']} is neighbored by 2+ CT zones (formerly controlled by {node_data.get('controlling_side', None)})")
    #             graph_did_change = True
    #         elif t_zone_neighbor_count >= 2 and ct_zone_neighbor_count == 0:
    #             node_data["controlling_side"] = "T"
    #             t_covered_area_ids.add(node_data["areaID"])
    #             # print(f"Zone {node_data['areaID']} is neighbored by 2+ T zones (formerly controlled by {node_data.get('controlling_side', None)})")
    #             graph_did_change = True

    return map_graph

def get_tile_area(area_id: int, map_name: str) -> float:
    """
    Returns the size of the area with the given ID
    """
    tile: dict = NAV[map_name][area_id]
    # Not using volume - using area because it's the GIF is more representative of area than volume
    # nw_corner: np.ndarray = np.array(tile["northWestX"], tile["northWestY"], tile["northWestZ"])
    # se_corner: np.ndarray = np.array(tile["southEastX"], tile["southEastY"], tile["southEastZ"])
    nw_corner: np.ndarray = np.array((tile["northWestX"], tile["northWestY"]))
    se_corner: np.ndarray = np.array((tile["southEastX"], tile["southEastY"]))
    dimensions: np.ndarray = np.absolute(np.subtract(nw_corner, se_corner))
    return np.prod(dimensions)


def calculate_controlled_area_sizes(map_graph: nx.Graph, map_name: str) -> dict[str, float]:
    """
    Returns a map of area_id to the number of players that are in that area
    """
    area_controlled_sizes: dict = {
        "CT": 0,
        "T": 0,
    }
    for node in map_graph.nodes(data=True):
        area_id: int = node[0]
        node_data: dict = node[1]
        if node_data["controlling_side"] == "CT":
            area_controlled_sizes["CT"] += get_tile_area(area_id, map_name)
        elif node_data["controlling_side"] == "T":
            area_controlled_sizes["T"] += get_tile_area(area_id, map_name)

    return area_controlled_sizes
