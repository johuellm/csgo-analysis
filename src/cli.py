from models.data_manager import EXAMPLE_DEMO_PATH, DataManager
from models.routine import DEFAULT_ROUTINE_LENGTH
from models.visualization_manager import VisualizationManager

def main():
    dm = DataManager.from_file(EXAMPLE_DEMO_PATH, do_validate=False)
    vizm = VisualizationManager.from_map(dm.get_map_name())

    team_routines = dm.get_all_team_routines(16, DEFAULT_ROUTINE_LENGTH)
    t_side_player_one_routines = team_routines.t_side.routines[0]
    for index, routine in enumerate(t_side_player_one_routines):
        print(f'x_{index}: {",".join(map(str, routine.x))}')
        print(f'y_{index}: {",".join(map(str, routine.y))}')

    t_side_player_one_first_routine = t_side_player_one_routines[0] 
    vizm.draw_routine(t_side_player_one_first_routine)
    vizm.render()
    input("Press Enter to end the program...")

if __name__ == '__main__':
    main()
