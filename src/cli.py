from models.data_manager import EXAMPLE_DEMO_PATH, DataManager
from models.position_tracker import PositionTracker
from models.routine import DEFAULT_ROUTINE_LENGTH
from models.routine_tracker import RoutineTracker, TilizedRoutine, aggregate_routines_from_directory
from models.visualization_manager import VisualizationManager
from awpy.visualization.plot import position_transform

def test_routine_drawing():
    dm = DataManager.from_file(EXAMPLE_DEMO_PATH, do_validate=False)
    vizm = VisualizationManager.from_data_manager(dm)

    team_routines = dm.get_all_team_routines(16, DEFAULT_ROUTINE_LENGTH)
    t_side_player_one_routines = team_routines.t_side.routines[0]
    for index, routine in enumerate(t_side_player_one_routines):
        print(f'x_{index}: {",".join(map(str, routine.x))}')
        print(f'y_{index}: {",".join(map(str, routine.y))}')

    t_side_player_one_first_routine = t_side_player_one_routines[0] 
    vizm.draw_routine(t_side_player_one_first_routine)
    vizm.render()
    input("Press Enter to end the program...")

def test_heatmap_generation():
    data_manager = DataManager.from_file(EXAMPLE_DEMO_PATH, do_validate=False)
    tracker = PositionTracker(data_manager.get_map_name(), 20)
    for round_index in range(data_manager.get_round_count()):
        for frame_index in range(data_manager.get_frame_count(round_index)):
            for player_list in data_manager.get_player_info_lists(round_index, frame_index).values():
                for player_info in player_list:
                    transformed_x, transformed_y = position_transform(tracker.map_name, player_info['x'], 'x'), position_transform(tracker.map_name, player_info['y'], 'y')
                    tracker.add_transformed_coordinates(transformed_x, transformed_y)
    vizm = VisualizationManager.from_data_manager(data_manager)
    vizm.draw_position_heatmap(tracker)
    vizm.render()
    input("Press Enter to end the program...")

def test_routine_heatmap():
    data_manager = DataManager.from_file(EXAMPLE_DEMO_PATH, do_validate=False)
    tile_length = 20
    # tracker = RoutineTracker(data_manager.get_map_name(), tile_length)
    tracker = aggregate_routines_from_directory(EXAMPLE_DEMO_PATH.parent / 'lan', data_manager.get_map_name(), tile_length, routine_length=DEFAULT_ROUTINE_LENGTH, limit=20)
    for round_index in range(data_manager.get_round_count()):
        team_routines = data_manager.get_all_team_routines(round_index, DEFAULT_ROUTINE_LENGTH)
        for team in (team_routines.t_side, team_routines.ct_side):
            for player_routines in team.routines:
                for routine in player_routines:
                    tracker.add_routine(TilizedRoutine(routine, tile_length))
    vizm = VisualizationManager.from_data_manager(data_manager)
    # Progressing the visualization to some arbitrary point in the game so the heatmap is more interesting than what it would look like from spawn positions.
    vizm.draw_round_start(0)
    for _ in range(25):
        vizm.progress_visualization()
    vizm.draw_routine_heatmap(tracker)
    vizm.render()
    input("Press Enter to end the program...")

if __name__ == '__main__':
    # test_routine_drawing()
    # test_heatmap_generation()
    test_routine_heatmap()
