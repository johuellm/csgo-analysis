import functools
import json
import pickle
import subprocess
import sys
import tkinter as tk
import tkinter.ttk as ttk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog

from awpy.visualization.plot import plot_map
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from models.data_manager import DataManager
from models.position_tracker import PositionTracker
from models.routine_tracker import RoutineTracker
from models.side_type import SideType
from models.visualization_manager import VisualizationManager
from predictor import Predictor
from tk_components.imports import CanvasTooltip
from tk_components.subcomponents import (
    FrameWithScrollableInnerFrame,
    HeatmapMenuButtonNames,
    PlayerInfoFrame,
    RoutineMenuButtonNames,
)

# TODO: Re-create more Noesis functionality.
# DONE 1. A bar on the bottom that has a list of round numbers. Selecting a round number shows the start of that round on the plot.
# DONE 2. A bar on the right that has a list of players. Each entry has their hp, armor, name, weapon, money, utility, and secondary. The HP is also visualized as a a bar (colored with the team color) that is filled in proportion to the player's HP.
# Note: consider turning some of the text into images for better readabiliity.
# DONE 3. A bar below the round-select bar, a scrubbable timeline that has markers for events that happened during the round. To the left of this bar is the pause/play button.
# DONE 4. A bar at the top that looks like: <Name of Team 1> - <Score of Team 1> | <Round Timer> | <Score of Team 2> - <Name of Team 2>. The team names and scores are updated as the rounds progress.
# DONE 5. Plot grenades (and their trajectories) on the map.

# After that, if I'm not missing any Noesis features, add the ability to plot a heatmap of trajectories from the entire dataset.


class MainApplication(ttk.Frame):
    """Parent frame for all non-root components. Must be attached to root."""

    root: tk.Tk
    dm: DataManager | None
    vm: VisualizationManager | None
    top_bar_menu: "TopBarMenu"
    game_state_label: "GameStateLabel"
    canvas: "CanvasPanel"
    player_status_sidebar: "PlayerStatusSidebar"
    round_select_bar: "RoundSelectBar"
    timeline_bar: "TimelineBar"
    tactics_sidebar: "TacticsSidebar"
    prediction_label: "PredictionLabel"

    def __init__(self, root: tk.Tk, *args, **kwargs):
        ttk.Frame.__init__(self, root, *args, **kwargs)
        self.root = root
        self.dm = None
        self.vm = None

        # Create GUI here
        self.top_bar_menu = TopBarMenu(self.root, self)
        self.top_bar_menu.pack(side="top", fill="x")

        self.prediction_label = PredictionLabel(self)
        self.prediction_label.pack(side="top", fill="x")

        self.timeline_bar = TimelineBar(self)
        self.timeline_bar.pack(side="bottom", fill="x")

        self.round_select_bar = RoundSelectBar(self)
        self.round_select_bar.pack(side="bottom", fill="x")

        self.tactics_sidebar = TacticsSidebar(self)
        self.tactics_sidebar.pack(side="right", fill="y")

        self.player_status_sidebar = PlayerStatusSidebar(self)
        self.player_status_sidebar.pack(side="right", fill="y")

        self.game_state_label = GameStateLabel(self)
        self.game_state_label.pack(side="top", fill="x")

        self.canvas = CanvasPanel(self)
        self.canvas.pack(side="top", fill="both", expand=True)

        self.pack(side="top", fill="both", expand=True)

    def load_file_and_reload(self, file_path: Path):
        """Re-initializes the DataManager, VisualizationManager, and relevant components after a new file is loaded."""
        self.dm = DataManager(file_path, do_validate=False)
        self.vm = VisualizationManager.from_data_manager(self.dm)
        self.canvas.draw_current_map()
        self.round_select_bar.update_round_list()
        self.prediction_label.clear_prediction()
        self.prediction_label.check_graphs()

        # Make sure there is a first round to draw before drawing it
        if self.dm.get_round_count() < 0:
            raise ValueError("No rounds found in the demo file.")

        # Draw the first round
        self.vm.draw_round_start(0)

        # Load tactics later because of a disk read conflict with prediction labels
        self.tactics_sidebar.load_tactic_labels_list()

        # Reload visualization widgets
        self.reload_visualization_widgets()

        # Enable the play button
        self.timeline_bar.reload_play_button()

    def reload_visualization_widgets(self):
        """Reload all relevant widgets to match the information in the current state of the visualization manager."""
        if self.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        # Canvas
        self.canvas.canvas.draw()

        # Game state label
        self.game_state_label.refresh_label()

        # Timeline bar
        self.timeline_bar.set_timeline_bar_progress(
            self.vm.current_round_index, self.vm.current_frame_index
        )

        self.prediction_label.get_prediction_for_frame(
            self.vm.current_round_index, self.vm.current_frame_index
        )

        # Player status sidebar
        # TODO: Update player info frames. Remove the lag because of this. Recursion depth exceeded error is caused.
        self.player_status_sidebar.update_player_info_frames()

    def exit(self):
        """Exits the application."""
        self.root.quit()
        self.root.destroy()


class TopBarMenu(ttk.Frame):
    """Top bar menu for the application. Must be attached to root."""

    root: tk.Tk
    main_app: MainApplication
    # Certain Menu objects need to be fields as they need to be accessed by other methods than just the constructor
    routine_menu: tk.Menu
    heatmap_menu: tk.Menu

    def __init__(self, root: tk.Tk, main_app: MainApplication, *args, **kwargs):
        ttk.Frame.__init__(self, root, *args, **kwargs)
        self.root = root
        self.main_app = main_app

        # Create GUI here

        # Create top bar
        top_bar = tk.Menu(self.root)
        self.root.config(menu=top_bar)

        # Create File menu
        file_menu = tk.Menu(top_bar, tearoff=False)
        top_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_demo_file)
        file_menu.add_command(label="Exit", command=self.main_app.exit)

        # Routine menu
        # All only possible if a demo is loaded
        # 1. Toggle routine visibility
        # 2. Set routine length

        routine_menu = tk.Menu(top_bar, tearoff=False)
        top_bar.add_cascade(label="Routines", menu=routine_menu)
        routine_menu.add_command(
            label=RoutineMenuButtonNames.TOGGLE_ROUTINE_VISUALIZATION.value,
            command=self.toggle_routine_visibility,
        )
        routine_menu.add_command(
            label=RoutineMenuButtonNames.SET_ROUTINE_LENGTH.value,
            command=self.ask_for_desired_routine_length,
        )

        routine_menu.entryconfigure(
            RoutineMenuButtonNames.TOGGLE_ROUTINE_VISUALIZATION.value, state=tk.DISABLED
        )
        routine_menu.entryconfigure(
            RoutineMenuButtonNames.SET_ROUTINE_LENGTH.value, state=tk.DISABLED
        )

        self.routine_menu = routine_menu

        # Heatmaps menu
        # Every option in here should be disabled if there is no demo loaded (i.e. DataManager is None)
        # Save RoutineTracker as file (pickle) (only possible if we've generated a RoutineTracker)
        # Load RoutineTracker from file (pickle)
        # ---
        # Generate PositionTracker object from current DataManager
        # Generate RoutineTracker object from current DataManager
        # Generate RoutineTracker object from all demos in a directory
        # ---
        # View list of demos contributing to the currently loaded RoutineTracker
        # ---
        # Display heatmap of player positions (via PositionTracker) (only possible if we've generated a PositionTracker object)
        # Display heatmap of player routines (via RoutineTracker) - as grid of tiles (only possible if we've generated a RoutineTracker object)
        # Display heatmap of player routines (via RoutineTracker) - as lines (only possible if we've generated a RoutineTracker object)
        # ---
        # Clear all heatmaps (only possible if we've displayed a heatmap)

        heatmap_menus = tk.Menu(top_bar, tearoff=False)
        top_bar.add_cascade(label="Heatmaps", menu=heatmap_menus)
        heatmap_menus.add_command(
            label=HeatmapMenuButtonNames.SAVE_HEATMAP_FILE.value,
            command=self.save_routine_heatmap_file,
        )
        heatmap_menus.add_command(
            label=HeatmapMenuButtonNames.LOAD_HEATMAP_FILE.value,
            command=self.load_routine_heatmap_file,
        )
        heatmap_menus.add_separator()
        heatmap_menus.add_command(
            label=HeatmapMenuButtonNames.GENERATE_POSITIONS_HEATMAP.value,
            command=self.create_position_heatmap_from_current_demo,
        )
        heatmap_menus.add_command(
            label=HeatmapMenuButtonNames.GENERATE_ROUTINES_HEATMAP.value,
            command=self.create_routine_heatmap_from_current_demo,
        )
        heatmap_menus.add_command(
            label=HeatmapMenuButtonNames.GENERATE_ROUTINES_HEATMAP_FROM_DIRECTORY.value,
            command=self.create_routine_heatmap_from_demo_directory,
        )
        heatmap_menus.add_separator()
        heatmap_menus.add_command(
            label=HeatmapMenuButtonNames.VIEW_ROUTINE_HEATMAP_COMPOSITION_INFO.value,
            command=self.view_routine_heatmap_composition_info,
        )
        heatmap_menus.add_separator()
        heatmap_menus.add_command(
            label=HeatmapMenuButtonNames.DRAW_POSITIONS_HEATMAP.value,
            command=self.display_position_heatmap,
        )
        heatmap_menus.add_command(
            label=HeatmapMenuButtonNames.DRAW_ROUTINES_HEATMAP_TILES.value,
            command=self.display_routine_tile_heatmap,
        )
        heatmap_menus.add_command(
            label=HeatmapMenuButtonNames.DRAW_ROUTINES_HEATMAP_LINES.value,
            command=self.display_routine_line_heatmap,
        )
        heatmap_menus.add_separator()
        heatmap_menus.add_command(
            label=HeatmapMenuButtonNames.CLEAR_HEATMAP.value,
            command=self.clear_heatmaps,
        )

        heatmap_menus.entryconfigure(
            HeatmapMenuButtonNames.SAVE_HEATMAP_FILE.value, state=tk.DISABLED
        )
        heatmap_menus.entryconfigure(
            HeatmapMenuButtonNames.LOAD_HEATMAP_FILE.value, state=tk.DISABLED
        )
        heatmap_menus.entryconfigure(
            HeatmapMenuButtonNames.GENERATE_POSITIONS_HEATMAP.value, state=tk.DISABLED
        )
        heatmap_menus.entryconfigure(
            HeatmapMenuButtonNames.GENERATE_ROUTINES_HEATMAP.value, state=tk.DISABLED
        )
        heatmap_menus.entryconfigure(
            HeatmapMenuButtonNames.GENERATE_ROUTINES_HEATMAP_FROM_DIRECTORY.value,
            state=tk.DISABLED,
        )
        heatmap_menus.entryconfigure(
            HeatmapMenuButtonNames.VIEW_ROUTINE_HEATMAP_COMPOSITION_INFO.value,
            state=tk.DISABLED,
        )
        heatmap_menus.entryconfigure(
            HeatmapMenuButtonNames.DRAW_POSITIONS_HEATMAP.value, state=tk.DISABLED
        )
        heatmap_menus.entryconfigure(
            HeatmapMenuButtonNames.DRAW_ROUTINES_HEATMAP_TILES.value, state=tk.DISABLED
        )
        heatmap_menus.entryconfigure(
            HeatmapMenuButtonNames.DRAW_ROUTINES_HEATMAP_LINES.value, state=tk.DISABLED
        )
        heatmap_menus.entryconfigure(
            HeatmapMenuButtonNames.CLEAR_HEATMAP.value, state=tk.DISABLED
        )

        self.heatmap_menu = heatmap_menus

        self.pack(side="top", fill="x")

    def open_demo_file(self):
        """Prompts user to select a .json file (ideally, this is the .json file corresponding to a CS:GO demo) and updates the main application's DataManager and VisualizationManager."""
        file_dialog_response = filedialog.askopenfilename(
            title="Select a CS:GO demo file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if file_dialog_response == "":
            # User cancelled the file dialog
            return
        file_path = Path(file_dialog_response)
        self.main_app.load_file_and_reload(file_path)

        # Re-disable every non-File menu option (because we want Open and Exit to always be available)
        for routine_menu_button in RoutineMenuButtonNames:
            self.routine_menu.entryconfigure(
                routine_menu_button.value, state=tk.DISABLED
            )
        for heatmap_menu_button in HeatmapMenuButtonNames:
            self.heatmap_menu.entryconfigure(
                heatmap_menu_button.value, state=tk.DISABLED
            )

        # Enable commands that only require a loaded DataManager
        self.routine_menu.entryconfigure(
            RoutineMenuButtonNames.TOGGLE_ROUTINE_VISUALIZATION.value, state=tk.NORMAL
        )
        self.routine_menu.entryconfigure(
            RoutineMenuButtonNames.SET_ROUTINE_LENGTH.value, state=tk.NORMAL
        )

        self.heatmap_menu.entryconfigure(
            HeatmapMenuButtonNames.LOAD_HEATMAP_FILE.value, state=tk.NORMAL
        )

        self.heatmap_menu.entryconfigure(
            HeatmapMenuButtonNames.GENERATE_POSITIONS_HEATMAP.value, state=tk.NORMAL
        )
        self.heatmap_menu.entryconfigure(
            HeatmapMenuButtonNames.GENERATE_ROUTINES_HEATMAP.value, state=tk.NORMAL
        )
        self.heatmap_menu.entryconfigure(
            HeatmapMenuButtonNames.GENERATE_ROUTINES_HEATMAP_FROM_DIRECTORY.value,
            state=tk.NORMAL,
        )

    def toggle_routine_visibility(self):
        """Toggles the visibility of player routines on the map."""
        if self.main_app.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        self.main_app.vm.toggle_routine_visualization()
        self.main_app.vm.revisualize()
        self.main_app.canvas.canvas.draw()

    def ask_for_desired_routine_length(self):
        """Prompts the user for a desired routine length and sets the VisualizationManager's routine length to that value."""
        if self.main_app.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        response = simpledialog.askinteger(
            "Set Routine Length",
            "Enter the desired routine length (in frames):",
            initialvalue=self.main_app.vm.visualized_routine_length,
        )
        if response is not None:
            if response <= 0:
                messagebox.showerror(
                    "Invalid Routine Length", "Routine length must be greater than 0."
                )
                return
            self.main_app.vm.visualized_routine_length = response

            # I imagine that if someone is changing the routine length, they want to see the routines
            self.main_app.vm.do_visualize_routines = True

            self.main_app.vm.revisualize()
            self.main_app.canvas.canvas.draw()

    def _enable_menu_options_requiring_loaded_routine_tracker(self):
        """Enables commands that require a loaded RoutineTracker object."""
        self.heatmap_menu.entryconfigure(
            HeatmapMenuButtonNames.SAVE_HEATMAP_FILE.value, state=tk.NORMAL
        )
        self.heatmap_menu.entryconfigure(
            HeatmapMenuButtonNames.VIEW_ROUTINE_HEATMAP_COMPOSITION_INFO.value,
            state=tk.NORMAL,
        )
        self.heatmap_menu.entryconfigure(
            HeatmapMenuButtonNames.DRAW_ROUTINES_HEATMAP_TILES.value, state=tk.NORMAL
        )
        self.heatmap_menu.entryconfigure(
            HeatmapMenuButtonNames.DRAW_ROUTINES_HEATMAP_LINES.value, state=tk.NORMAL
        )

    def save_routine_heatmap_file(self):
        """Prompts the user for a file path and saves the routine heatmap data to a file."""
        if self.main_app.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.main_app.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        if self.main_app.vm._routine_tracker is None:
            messagebox.showerror(
                "No Routine Heatmap Data",
                "No routine heatmap data has been generated to save.",
            )
            return

        initial_file_name = f"{self.main_app.dm.get_map_name()}.rhd"
        file_dialog_response = filedialog.asksaveasfilename(
            title="Save Routine Heatmap Data",
            filetypes=[("Routine Heatmap Data files", "*.rhd"), ("All files", "*.*")],
            initialfile=initial_file_name,
        )
        if file_dialog_response == "":
            # User cancelled the file dialog
            return
        file_path = Path(file_dialog_response)
        with file_path.open("wb") as output_file:
            pickle.dump(self.main_app.vm._routine_tracker, output_file)
        messagebox.showinfo(
            "Routine Heatmap Data Saved", "Routine heatmap data saved successfully."
        )

    def load_routine_heatmap_file(self):
        """Asks the user for a file path and loads a routine heatmap file."""
        if self.main_app.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.main_app.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        file_dialog_response = filedialog.askopenfilename(
            title="Load Routine Heatmap Data",
            filetypes=[("Routine Heatmap Data files", "*.rhd"), ("All files", "*.*")],
        )
        if file_dialog_response == "":
            # User cancelled the file dialog
            return
        file_path = Path(file_dialog_response)
        with file_path.open("rb") as input_file:
            routine_tracker = pickle.load(input_file)
        if not isinstance(routine_tracker, RoutineTracker):
            messagebox.showerror(
                "Invalid File",
                "The loaded file did not contain valid routine heatmap data. Cancelled loading operation.",
            )
            raise ValueError("Loaded file is not a RoutineTracker object.")
        if routine_tracker.map_name != self.main_app.dm.get_map_name():
            messagebox.showerror(
                "Map Mismatch",
                f"The loaded routine heatmap data is for a different map ({routine_tracker.map_name}) than the currently loaded demo ({self.main_app.dm.get_map_name()}). Cancelled loading operation.",
            )
            raise ValueError("Loaded RoutineTracker object is for a different map.")
        self.main_app.vm._routine_tracker = routine_tracker
        messagebox.showinfo(
            "Routine Heatmap Data Loaded",
            f"Routine heatmap data loaded successfully, including data from {len(routine_tracker.metadata)} demos.",
        )

        self._enable_menu_options_requiring_loaded_routine_tracker()

    def create_position_heatmap_from_current_demo(self):
        """Creates a heatmap of player positions from the current demo."""
        if self.main_app.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.main_app.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        tracker = PositionTracker.from_data_manager(self.main_app.dm, 20)
        self.main_app.vm._position_tracker = tracker

        # Enable position heatmap drawing
        self.heatmap_menu.entryconfigure(
            HeatmapMenuButtonNames.DRAW_POSITIONS_HEATMAP.value, state=tk.NORMAL
        )

    def create_routine_heatmap_from_current_demo(self):
        """Creates a heatmap of player routines from the current demo."""
        if self.main_app.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.main_app.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        tracker = RoutineTracker.from_data_manager(self.main_app.dm, 20)
        self.main_app.vm._routine_tracker = tracker

        self._enable_menu_options_requiring_loaded_routine_tracker()

    def create_routine_heatmap_from_demo_directory(self):
        """Creates a heatmap of player routines from all demos in a directory."""
        if self.main_app.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.main_app.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        file_dialog_response = filedialog.askdirectory(
            title="Select a directory containing CS:GO demo files"
        )
        if file_dialog_response == "":
            # User cancelled the file dialog
            return
        directory_path = Path(file_dialog_response)
        tracker = RoutineTracker.aggregate_routines_from_directory(
            directory_path, self.main_app.dm.get_map_name(), 20
        )
        self.main_app.vm._routine_tracker = tracker

        # TODO: Add a progress bar that displays during the aggregation process (can be the 'indeterminate' style, as we might not be able to have insight into the progress of `aggregate_routines_from_directory`)
        messagebox.showinfo(
            "Routine Heatmap Data Loaded",
            f"Routine heatmap data loaded successfully, including data from {len(tracker.metadata)} demos.",
        )

        self._enable_menu_options_requiring_loaded_routine_tracker()

    def view_routine_heatmap_composition_info(self):
        """Displays a list of demos used in the creation of the current routine heatmap."""
        if self.main_app.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.main_app.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        routine_tracker = self.main_app.vm._routine_tracker
        if routine_tracker is None:
            messagebox.showerror(
                "No Routine Heatmap Data",
                "No routine heatmap data is currently loaded. Cannot display composition info.",
            )
            raise ValueError("No RoutineTracker object loaded.")

        # Create a table of demo metadata and display it in a new window
        composition_info_window = tk.Toplevel(self.root)
        composition_info_window.title(
            f"Routine Heatmap Composition Info - {routine_tracker.map_name} - {len(routine_tracker.metadata)} Demos Used"
        )
        composition_info_window.geometry("1200x700")
        composition_info_window.focus()
        composition_info_window.grab_set()  # Prevent interaction with the main window while this window is open - this is so that the user doesn't modify the RoutineTracker object while viewing its composition info

        scrolling_frame_container = FrameWithScrollableInnerFrame(
            composition_info_window
        )
        scrollable_frame = scrolling_frame_container.scrollable_frame

        def show_file_in_explorer(path: Path):
            """Opens the system's native file explorer to the given path's directory and selects it."""
            match sys.platform:
                case "win32":
                    subprocess.Popen(["explorer", "/select,", path.absolute()])
                case "darwin":
                    subprocess.Popen(
                        ["open", "--", path.absolute()]
                    )  # NOTE - I did not test this as I do not have a Mac
                case "linux":
                    subprocess.Popen(
                        ["xdg-open", "--", path.absolute()]
                    )  # NOTE - I did not test this
                case _:
                    messagebox.showerror(
                        "Unsupported Platform",
                        f"Opening native file explorer is not supported on platform {sys.platform}.",
                    )
                    raise NotImplementedError(
                        f"Opening native file explorer is not supported on platform {sys.platform}."
                    )

        # Get the first metadata object to get the fields for the table
        table_fields = routine_tracker.metadata[0].get_fields_for_table().keys()
        for i, field_key in enumerate(table_fields):
            field_label = tk.Entry(scrollable_frame, font=("Arial", 12, "bold"))
            field_label.grid(row=0, column=i)
            field_label.insert(tk.END, field_key)
            field_label.config(state="readonly")

        for i, demo_metadata in enumerate(routine_tracker.metadata, start=1):
            for j, field_entry in enumerate(
                demo_metadata.get_fields_for_table().items()
            ):
                field_value = field_entry[1]
                field_label = tk.Entry(scrollable_frame, font=("Arial", 12))
                field_label.grid(row=i, column=j)
                field_label.insert(tk.END, str(field_value))
                field_label.config(state="readonly")
                if field_entry[0] == "File Name":
                    # We want the file name to be clickable (opening the native file explorer to the file's directory and selecting it)
                    # So, make this cell look clickable
                    field_label.config(
                        fg="blue",
                        cursor="hand2",
                        relief="raised",
                        font=("Arial", 12, "underline"),
                    )
                    field_label.bind(
                        "<Button-1>",
                        lambda e, path=demo_metadata.path: show_file_in_explorer(path),
                    )  # The path is a parameter to the lambda function so that it is captured by the closure - otherwise, the lambda function would use the last value of `path` in the loop

        scrollable_frame.pack(fill="both", expand=True)
        scrolling_frame_container.pack(fill="both", expand=True)

    def display_position_heatmap(self):
        """Displays a heatmap of player positions."""
        if self.main_app.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.main_app.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        self.main_app.vm.draw_position_heatmap()
        self.main_app.canvas.canvas.draw()

        # Enable heatmap clearing
        self.heatmap_menu.entryconfigure(
            HeatmapMenuButtonNames.CLEAR_HEATMAP.value, state=tk.NORMAL
        )

    def display_routine_tile_heatmap(self):
        """Displays a heatmap of player routines as a grid of tiles."""
        if self.main_app.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.main_app.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        self.main_app.vm.draw_routine_tile_heatmap()
        self.main_app.canvas.canvas.draw()

        # Enable heatmap clearing
        self.heatmap_menu.entryconfigure(
            HeatmapMenuButtonNames.CLEAR_HEATMAP.value, state=tk.NORMAL
        )

    def display_routine_line_heatmap(self):
        """Displays a heatmap of player routines as lines."""
        if self.main_app.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.main_app.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        self.main_app.vm.draw_routine_line_heatmap()
        self.main_app.canvas.canvas.draw()

        # Enable heatmap clearing
        self.heatmap_menu.entryconfigure(
            HeatmapMenuButtonNames.CLEAR_HEATMAP.value, state=tk.NORMAL
        )

    def clear_heatmaps(self):
        """Clears all heatmaps."""
        if self.main_app.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.main_app.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        self.main_app.vm.clear_heatmap_drawings()
        self.main_app.canvas.canvas.draw()

        # Disable heatmap clearing
        self.heatmap_menu.entryconfigure(
            HeatmapMenuButtonNames.CLEAR_HEATMAP.value, state=tk.DISABLED
        )


class CanvasPanel(ttk.Frame):
    """Panel for displaying plots."""

    parent: MainApplication
    canvas: FigureCanvasTkAgg

    _do_play_visualization: bool

    def __init__(self, parent: MainApplication, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self._do_play_visualization = False

        # Create GUI here
        default_figure, _ = plot_map(map_type="simpleradar")
        self.canvas = FigureCanvasTkAgg(
            default_figure, self
        )  # Note: this instantiation is problematic - see the comment in main() in src/gui.py. Figure out a way to fix this at some point.
        self.__prep_canvas_widget()

        self.pack(side="top", fill="both", expand=True)

    def __prep_canvas_widget(self):
        """Adds key press functionality and packs the canvas widget."""
        self.canvas.mpl_connect(
            "key_press_event", lambda event: key_press_handler(event, self.canvas)
        )
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    def draw_current_map(self):
        """Ensures there is a map loaded in the VisualizationManager and then draws it."""
        if self.parent.vm is None:
            raise ValueError("VisualizationManager not initialized.")
        # Remove the current canvas before creating the new one so there aren't two
        self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(self.parent.vm.fig, self)
        self.__prep_canvas_widget()

    def draw_round(self, round_index: int):
        """Draws the map at the start of the given round number."""
        if self.parent.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.parent.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        # Draw on map canvas
        self.parent.vm.draw_round_start(round_index)
        self.canvas.draw()

    def play_visualization(self):
        """Plays the visualization."""
        if self.parent.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.parent.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        self._do_play_visualization = True
        self._tick_visualization()

    def _tick_visualization(self):
        """Progresses the visualization by one frame."""
        if self.parent.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.parent.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        # Progress the visualization
        self.parent.vm.progress_visualization()
        # Reload widgets
        self.parent.reload_visualization_widgets()

        if self._do_play_visualization:
            # Calculating the number of milliseconds a frame should be displayed for (i.e. the seconds per frame)
            # Dividing tick rate (ticks / second) by parse rate (ticks / frame) gives frames / second:
            # frames / second = T ticks / 1 second (tick rate) * 1 frame / S ticks (parse rate) = T / S
            # To see the number of seconds for which a frame should be displayed, we take the reciprocal of the frames / second:
            # -> seconds / frame = S / T
            # To convert this to the number of milliseconds a frame should be displayed for, we multiply by 1000:
            # -> milliseconds / frame = 1000 * (S / T)
            parse_rate = self.parent.dm.get_parse_rate()
            tick_rate = self.parent.dm.get_tick_rate()
            milliseconds_per_frame = int((parse_rate / tick_rate) * 1000)
            self.parent.root.after(milliseconds_per_frame, self._tick_visualization)

    def pause_visualization(self):
        """Pauses the visualization."""
        self._do_play_visualization = False


class RoundSelectBar(ttk.Frame):
    """A bar that displays a list of the round numbers from the selected demo. Selecting a round number shows the start of that round on the plot."""

    parent: MainApplication

    def __init__(self, parent: MainApplication, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        # Initialize empty button storage list
        self.round_buttons: list[tk.Button] = []

        # Create GUI here
        self._create_round_buttons()

        self.pack(side="top", fill="x")

    def _create_round_buttons(self):
        """Creates buttons for each round in the selected demo. If no demo is selected, creates a dummy set of 25 disabled buttons."""
        round_count = 31 if self.parent.dm is None else self.parent.dm.get_round_count()
        button_state = "disabled" if self.parent.dm is None else "normal"

        self.round_buttons.clear()  # Clear old references

        for round_index in range(round_count):
            # Add a button for each round
            round_number = round_index + 1
            # If interested in using ttk.Button here, note that a row of the tk.Buttons, when resized to be smaller, will shrink all buttons equally until reaching a minimum size. After that, then higher round number buttons will be hidden.
            # With the new ttk.Buttons, the higher round number buttons will be hidden immediately, i.e. there is no attempt to shrink all buttons equally.
            # Fix this resizing issue if interested in using ttk.Buttons.
            round_button = tk.Button(
                self,
                text=f"{round_number}",
                command=functools.partial(self._go_to_round, round_index),
                state=button_state,
            )
            round_button.pack(side="left", fill="x", expand=True)
            self.round_buttons.append(round_button)

    def _go_to_round(self, round_index: int):
        """Updates the visualization to show the start of the round specified by `round_index`."""
        self.parent.canvas.draw_round(round_index)
        self.parent.reload_visualization_widgets()

    def disable_round_button(self, round_index: int):
        """"""
        if 0 <= round_index < len(self.round_buttons):
            self.round_buttons[round_index].configure(state="disabled")

    def update_round_list(self):
        """Updates the list of round buttons."""
        for widget in self.winfo_children():
            widget.destroy()
        self._create_round_buttons()


class TimelineBar(ttk.Frame):
    """A bar that displays a scrubbable timeline with markers for events that happened during the round."""

    parent: MainApplication
    _play_pause_button: ttk.Button
    _timeline_canvas: tk.Canvas
    visualized_round_index: int | None

    def __init__(self, parent: MainApplication, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        # Initialize empty selection
        self.selection_active = False
        self.selection_start_frame = None
        self.selection_end_frame = None
        self.selection_marker = None
        self.selection_drag_side = None

        # Create GUI here

        # Play button
        self._create_play_button()

        # Timeline bar
        self._create_timeline_bar()

        self.pack(side="top", fill="x")

    def call_play_visualization(self):
        """Tells the CanvasPanel to play the visualization and replaces the play button with a pause button."""
        self.parent.canvas.play_visualization()
        self.reload_play_button(create_pause_button=True)

    def call_pause_visualization(self):
        """Tells the CanvasPanel to pause the visualization and replaces the pause button with a play button."""
        self.parent.canvas.pause_visualization()
        self.reload_play_button()

    def _create_play_button(self):
        """Creates the play button."""
        play_button = ttk.Button(
            self,
            text="Play",
            command=self.call_play_visualization,
            state="disabled" if self.parent.dm is None else "normal",
        )
        play_button.pack(side="left", fill="y")
        self._play_pause_button = play_button

    def reload_play_button(self, create_pause_button: bool = False):
        """Reloads the play button. If `create_pause_button` is True, creates a pause button instead of a play button."""
        if create_pause_button:
            self._play_pause_button.configure(
                text="Pause", command=self.call_pause_visualization
            )
        else:
            self._play_pause_button.configure(
                text="Play",
                command=self.call_play_visualization,
                state="disabled" if self.parent.dm is None else "normal",
            )

    def _create_timeline_bar(self, round_index: int | None = None):
        """Creates the timeline bar."""

        timeline_canvas = tk.Canvas(
            self, height=100, bg="white", border=0, borderwidth=0
        )
        self._timeline_canvas = timeline_canvas
        timeline_canvas.pack(side="left", fill="x", expand=True)

        # Add scrubbing functionality
        timeline_canvas.bind(
            "<Button-1>", self._jump_to_frame
        )  # A single click of Mouse 1
        timeline_canvas.bind(
            "<B1-Motion>", self._jump_to_frame
        )  # Holding Mouse 1 down and dragging

        # Add selection functionality
        timeline_canvas.bind("<B3-Motion>", self._select_frame)
        # Delete selection
        timeline_canvas.bind("<Button-2>", self._deselect_frames)

        timeline_canvas.bind(
            "<Button-5>",
            lambda e: self._jump_to_frame(
                frame_index=max(0, self.parent.vm.current_frame_index - 1)
            ),
        )
        timeline_canvas.bind(
            "<Button-4>",
            lambda e: self._jump_to_frame(
                frame_index=min(
                    self.parent.dm.get_frame_count(self.visualized_round_index) - 1,
                    self.parent.vm.current_frame_index + 1,
                )
            ),
        )
        timeline_canvas.bind(
            "<MouseWheel>",
            lambda e: self._jump_to_frame(
                frame_index=(
                    max(0, self.parent.vm.current_frame_index - 1)
                    if e.delta > 0
                    else min(
                        self.parent.dm.get_frame_count(self.visualized_round_index) - 1,
                        self.parent.vm.current_frame_index + 1,
                    )
                )
            ),
        )
        timeline_canvas.bind("<ButtonRelease-3>", self.selection_button_release)
        self.visualized_round_index = round_index

        if round_index is not None:
            self._add_event_markers(round_index)
            self.load_timeline_tactics(round_index)
            self.load_timeline_predictions(round_index)

    def _get_pixels_per_frame(self, round_index: int):
        """Returns the number of horizontal pixels in the timeline bar canvas allocated to each frame in round specified by `round_index`."""
        if self.parent.dm is None:
            raise ValueError("DataManager not initialized.")

        total_frames_in_round = self.parent.dm.get_frame_count(round_index)
        canvas_width = self._timeline_canvas.winfo_width()
        return canvas_width / total_frames_in_round

    def _jump_to_frame(self, event: tk.Event = None, frame_index: int = None):
        """Sets the current frame of the visualization to the frame that corresponds to the point clicked on in the timeline bar. Doesn't do anything if no demo is loaded."""
        if self.parent.dm is None:
            return
        if self.parent.vm is None:
            return
        if self.visualized_round_index is None:
            return

        """
        # Check if the click was within the bounds of the timeline bar
        if event.x < 0 or event.x > self._timeline_canvas.winfo_width():
            return

        # Calculate which frame corresponds to the x-coordinate of the click
        clicked_frame_index = int(
            event.x / self._get_pixels_per_frame(self.visualized_round_index)
        )
        """
        if frame_index is None:
            if event is None:
                return
            if event.x < 0 or event.x > self._timeline_canvas.winfo_width():
                return
            frame_index = int(
                event.x / self._get_pixels_per_frame(self.visualized_round_index)
            )  # Clicked frame index
        total_frames = self.parent.dm.get_frame_count(self.visualized_round_index)
        frame_index = max(0, min(frame_index, total_frames - 1))

        # Jump to that frame in the visualization
        self.parent.vm.current_frame_index = frame_index
        # Update the plot
        self.parent.vm.revisualize()
        # Reload visualization widgets
        self.parent.reload_visualization_widgets()

    def _select_frame(self, event: tk.Event):
        """Selects a portion of frames on the timeline bar and sets the current frame in the visualization."""
        if self.parent.dm is None:
            return
        if self.parent.vm is None:
            return
        if self.visualized_round_index is None:
            return

        # Check if the click was within the bounds of the timeline bar
        if event.x < 0 or event.x > self._timeline_canvas.winfo_width():
            return

        frame_index = int(
            event.x / self._get_pixels_per_frame(self.visualized_round_index)
        )

        if not self.selection_active:
            # Initial selection start
            self.selection_start_frame = frame_index
            self.selection_end_frame = frame_index
            self.selection_active = True
            self.selection_drag_side = None
        else:
            # If already active, decide which side to update
            if self.selection_drag_side is None:
                dist_to_start = abs(frame_index - self.selection_start_frame)
                dist_to_end = abs(frame_index - self.selection_end_frame)
                self.selection_drag_side = (
                    "start" if dist_to_start < dist_to_end else "end"
                )

            if self.selection_drag_side == "start":
                self.selection_start_frame = frame_index
            else:
                self.selection_end_frame = frame_index

        start = min(self.selection_start_frame, self.selection_end_frame)
        end = max(self.selection_start_frame, self.selection_end_frame) + 1

        pixels_per_frame = self._get_pixels_per_frame(self.visualized_round_index)
        x_start = int(start * pixels_per_frame)
        x_end = int(end * pixels_per_frame)

        # Remove previous selection marker if it exists
        if self.selection_marker:
            self._timeline_canvas.delete(self.selection_marker)

        timeline_height_center = int(self._timeline_canvas.winfo_height() / 2)

        # Draw new selection marker
        self.selection_marker = self._timeline_canvas.create_rectangle(
            x_start,
            timeline_height_center - 30,
            x_end,
            timeline_height_center + 30,
            fill="lightblue",
            stipple="gray12",
            outline="gray",
            tags="selection",
        )

        # Jump to that frame in the visualization
        self.parent.vm.current_frame_index = frame_index
        # Update the plot
        self.parent.vm.revisualize()
        # Reload visualization widgets
        self.parent.reload_visualization_widgets()

    def selection_button_release(self, event: tk.Event):
        self.selection_drag_side = None

    def _deselect_frames(self, event: tk.Event = None):
        if self.selection_marker:
            self._timeline_canvas.delete(self.selection_marker)
        self.selection_active = False
        self.selection_start_frame = None
        self.selection_end_frame = None
        self.selection_drag_side = None

    def _add_event_markers(self, round_index: int):
        """Adds markers to the timeline bar for each event that happened during the round specified by `round_index`."""
        if self.parent.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.parent.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        round_events = self.parent.dm.get_round_events(round_index)
        round_starting_tick = self.parent.dm.get_round_start_tick(round_index)
        pixels_per_tick = (
            self._timeline_canvas.winfo_width()
            / self.parent.dm.get_round_active_tick_length(round_index)
        )

        kill_event_color: dict[SideType, str] = {
            SideType.T: "goldenrod",
            SideType.CT: "steelblue",
        }

        # Only drawing kill + bomb events for now
        for event in round_events.kills:
            victim_team = SideType.from_str(event["victimSide"] or "")
            x = int((event["tick"] - round_starting_tick) * pixels_per_tick)
            kill_event_marker = self._timeline_canvas.create_line(
                x,
                0,
                x,
                self._timeline_canvas.winfo_height(),
                fill=kill_event_color[victim_team],
                tags="kill-event",
                width=2,
                activewidth=3,
            )
            tooltip_text = f'{event["attackerName"]} killed {event["victimName"]} with {event["weapon"]}'
            CanvasTooltip(self._timeline_canvas, kill_event_marker, text=tooltip_text)

        for event in round_events.bomb_events:
            x = int((event["tick"] - round_starting_tick) * pixels_per_tick)
            bomb_event_marker = self._timeline_canvas.create_line(
                x,
                0,
                x,
                self._timeline_canvas.winfo_height(),
                fill="red",
                tags="bomb-event",
                width=2,
                activewidth=3,
            )
            tooltip_text = f'Bomb action {event["bombAction"]} by {event["playerName"]}'
            CanvasTooltip(self._timeline_canvas, bomb_event_marker, text=tooltip_text)

        self._timeline_canvas.update()

    def reset_timeline_bar(self, round_index: int | None = None):
        """Resets the timeline bar to its default state. If `round_index` is not None, adds event markers for the round specified by `round_index`."""
        self._timeline_canvas.delete("all")
        self._timeline_canvas.update()
        self.visualized_round_index = round_index
        if round_index is not None:
            self._add_event_markers(round_index)
            self.load_timeline_tactics(round_index)
            self.load_timeline_predictions(round_index)

    def _draw_progress_bar_fill_rectangle(self, x: int, y: int):
        """Draws a rectangle in the progress bar starting from the left and ending at the x-coordinate specified by `x`."""
        self._timeline_canvas.delete("progress")
        self._timeline_canvas.delete("progress_current_frame")
        self._timeline_canvas.create_rectangle(
            0,
            0,
            x,
            self._timeline_canvas.winfo_height(),
            fill="lightgray",
            outline="",
            tags="progress",
        )
        self._timeline_canvas.tag_lower(
            "progress"
        )  # Lower the progress bar along the z-axis so that it doesn't cover the event markers
        self._timeline_canvas.create_rectangle(
            x,
            0,
            y,
            self._timeline_canvas.winfo_height(),
            fill="silver",
            outline="",
            tags="progress_current_frame",
        )
        self._timeline_canvas.tag_lower("progress_current_frame")
        self._timeline_canvas.update()

    def set_timeline_bar_progress(self, round_index: int, current_frame_index: int = 0):
        """Fills the timeline bar to indicate the progress of the visualized round, calculating how far the bar needs to visually progress by calculating how many ticks happened in the round specified by `round_index`."""
        if self.parent.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.parent.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        # Check if the visualized round has changed, as this will require a reset of the timeline bar
        if self.visualized_round_index != round_index:
            self.visualized_round_index = round_index
            self.reset_timeline_bar(round_index)
            self._add_event_markers(round_index)
            self.load_timeline_tactics(round_index)
            self.load_timeline_predictions(round_index)

            # Refresh round select bar as well
            self.parent.round_select_bar.update_round_list()
            self.parent.round_select_bar.disable_round_button(round_index)

        # Paint the canvas up to current_frame_index * pixels_per_tick in gray to indicate progress
        progress_bar_fill_length = int(
            current_frame_index * self._get_pixels_per_frame(round_index)
        )
        previewed_frame_end = int(
            (current_frame_index + 1) * self._get_pixels_per_frame(round_index)
        )
        self._draw_progress_bar_fill_rectangle(
            progress_bar_fill_length, previewed_frame_end
        )

    def load_timeline_tactics(self, round_index: int):
        if self.parent.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.parent.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        round_index_adjusted = round_index + 1

        match_id = self.parent.dm.get_match_id()
        output_file = (
            Path.cwd()
#            / "research_project"
            / "tactic_labels"
            / f"{self.parent.dm.get_map_name()}"
            / match_id
            / f"{match_id}_{round_index_adjusted}.json"
        )

        if not output_file.exists():
            return

        with open(output_file, "r") as f:
            round_tactic_data = json.load(f)

        if not round_tactic_data:
            return

        pixels_per_frame = self._get_pixels_per_frame(round_index)

        # Force re-sort frames
        sorted_frames = sorted(
            (int(frame), tactic) for frame, tactic in round_tactic_data.items()
        )

        segments = []
        current_tactic = None
        start_frame = None
        last_frame = None

        for frame, tactic in sorted_frames:
            if current_tactic is None:  # Start segment
                current_tactic = tactic
                start_frame = frame
                last_frame = frame
            elif (
                tactic == current_tactic and frame == last_frame + 1
            ):  # Continue segment
                last_frame = frame
            else:  # Save segment and start again
                segments.append((start_frame, last_frame, current_tactic))

                current_tactic = tactic
                start_frame = frame
                last_frame = frame

        if current_tactic is not None:  # Add final segment
            segments.append((start_frame, last_frame, current_tactic))

        alternate_color = False
        for start_frame, last_frame, tactic in segments:
            if alternate_color:
                tactic_color = "darkgoldenrod"
                alternate_color = not alternate_color
            else:
                tactic_color = "goldenrod"
                alternate_color = not alternate_color
            last_frame += 1  # Adjust to cover the last frame of the tactic
            tactic_start_position = start_frame * pixels_per_frame
            tactic_end_position = last_frame * pixels_per_frame
            tactic_label_position = ((start_frame + last_frame) / 2) * pixels_per_frame
            tactic_marker = self._timeline_canvas.create_line(
                tactic_start_position,
                int((self._timeline_canvas.winfo_height() / 2) - 20),
                tactic_end_position,
                int((self._timeline_canvas.winfo_height() / 2) - 20),
                fill=tactic_color,
                width=10,
                activewidth=15,
                tags="test",
            )
            tooltip_text = f"{tactic}"
            CanvasTooltip(self._timeline_canvas, tactic_marker, text=tooltip_text)
            self._timeline_canvas.create_text(
                tactic_label_position,
                int((self._timeline_canvas.winfo_height() / 2) - 36),
                text=f"{tactic}",
                fill=tactic_color,
            )
        self._timeline_canvas.update()

    def load_timeline_predictions(self, round_index: int):
        if self.parent.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.parent.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        if not self.parent.prediction_label.predictor_output:
            return

        # match_id = self.parent.dm.get_match_id()

        predictor_output = self.parent.prediction_label.predictor_output

        pixels_per_frame = self._get_pixels_per_frame(round_index)

        segments = []
        current_tactic = None
        start_frame = None
        last_frame = None

        for frame, tactic in enumerate(predictor_output[round_index]):
            if current_tactic is None:  # Start segment
                current_tactic = tactic
                start_frame = frame
                last_frame = frame
            elif (
                tactic == current_tactic and frame == last_frame + 1
            ):  # Continue segment
                last_frame = frame
            else:  # Save segment and start again
                segments.append((start_frame, last_frame, current_tactic))

                current_tactic = tactic
                start_frame = frame
                last_frame = frame

        if current_tactic is not None:  # Add final segment
            segments.append((start_frame, last_frame, current_tactic))

        alternate_color = False
        for start_frame, last_frame, tactic in segments:
            if alternate_color:
                tactic_color = "steelblue4"
                label_spacing = -26
                alternate_color = not alternate_color
            else:
                tactic_color = "steelblue3"
                label_spacing = 0
                alternate_color = not alternate_color
            last_frame += 1  # Adjust to cover the last frame of the tactic
            tactic_start_position = start_frame * pixels_per_frame
            tactic_end_position = last_frame * pixels_per_frame
            tactic_label_position = ((start_frame + last_frame) / 2) * pixels_per_frame
            tactic_marker = self._timeline_canvas.create_line(
                tactic_start_position,
                int((self._timeline_canvas.winfo_height() / 2) + 20),
                tactic_end_position,
                int((self._timeline_canvas.winfo_height() / 2) + 20),
                fill=tactic_color,
                width=10,
                activewidth=15,
                tags="test2",
            )
            tooltip_text = f"{tactic}"
            CanvasTooltip(self._timeline_canvas, tactic_marker, text=tooltip_text)
            self._timeline_canvas.create_text(
                tactic_label_position,
                int((self._timeline_canvas.winfo_height() / 2) + 31 + label_spacing),
                text=f"{tactic}",
                fill=tactic_color,
            )
        self._timeline_canvas.update()


class GameStateLabel(ttk.Frame):
    """A label that displays the current game state."""

    parent: MainApplication
    label: tk.Text

    def __init__(self, parent: MainApplication, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.label = tk.Text(self, font=("Arial", 14), height=1, wrap="none")

        # Add format tags we want to use
        self.label.tag_configure("center", justify="center")
        self.label.tag_configure("t", foreground="goldenrod")
        self.label.tag_configure("ct", foreground="darkblue")

        self.label.insert(tk.END, "T - 0", ("t", "center"))
        self.label.insert(tk.END, " | 0:00 | ", "center")
        self.label.insert(tk.END, "0 - CT", ("ct", "center"))

        # Disable the label so it can't be edited
        self.label.configure(state=tk.DISABLED)

        self.label.pack(side="top", fill="x", expand=True)

        self.pack(side="top", fill="x")

    def _format_info_label(self, team_name: str, score: int, side: SideType):
        """Formats the team info label based on the given side."""
        match side:
            case SideType.T:
                return f"{team_name} - {score}"
            case SideType.CT:
                return f"{score} - {team_name}"

    def refresh_label(self):
        """Refreshes the label with the current game state."""
        if self.parent.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.parent.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        currently_visualized_round = self.parent.vm.current_round_index
        current_frame = self.parent.vm.current_frame_index

        team_names = self.parent.dm.get_team_names(currently_visualized_round)
        team_scores = self.parent.dm.get_team_scores(currently_visualized_round)
        clock_time = self.parent.dm.get_clock_time(
            currently_visualized_round, current_frame
        )

        # Re-enable the label's editable status so we can update it
        self.label.configure(state=tk.NORMAL)

        self.label.delete("1.0", tk.END)
        self.label.insert(
            tk.END, f"{team_names.t_team_name} - {team_scores.t_score}", ("t", "center")
        )
        self.label.insert(tk.END, f" | {clock_time} | ", "center")
        self.label.insert(
            tk.END,
            f"{team_scores.ct_score} - {team_names.ct_team_name}",
            ("ct", "center"),
        )

        # Disable the label again
        self.label.configure(state=tk.DISABLED)


class PlayerStatusSidebar(ttk.Frame):
    """A sidebar that displays player information."""

    parent: MainApplication
    player_info_frames: list[PlayerInfoFrame]

    def __init__(self, parent: MainApplication, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        # Create GUI here
        self.player_info_frames = []
        for _ in range(10):
            player_info_frame = PlayerInfoFrame(self)
            player_info_frame.pack(side="top", fill="x")
            self.player_info_frames.append(player_info_frame)

        self.pack(side="right", fill="y")

    def update_player_info_frames(self):
        if self.parent.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.parent.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        current_round = self.parent.vm.current_round_index
        current_frame = self.parent.vm.current_frame_index

        info = self.parent.dm.get_player_info_lists(current_round, current_frame)

        # Creating a map of player names to their corresponding PlayerInfoFrame objects for faster lookup
        player_info_frame_map: dict[str, PlayerInfoFrame] = {
            frame.player_name: frame for frame in self.player_info_frames
        }
        player_names = set(
            [player["name"] for player in info[SideType.CT] + info[SideType.T]]
        )

        # If the set of player names is different from what the frames are currently displaying, we know that not every player has a frame allocated to them.
        # So, re-assign all of the frames to this new set of players.
        do_forget_previous_owner = False
        previous_frame_owners = set(player_info_frame_map.keys())
        if previous_frame_owners != player_names:
            do_forget_previous_owner = True

        if do_forget_previous_owner:
            for index, player in enumerate(info[SideType.CT]):
                self.player_info_frames[index].player_name = player["name"]
                self.player_info_frames[index].set_info(player)

            for index, player in enumerate(info[SideType.T], start=5):
                self.player_info_frames[index].player_name = player["name"]
                self.player_info_frames[index].set_info(player)
        else:
            for player in info[SideType.CT]:
                player_info_frame_map[player["name"]].set_info(player)

            for player in info[SideType.T]:
                player_info_frame_map[player["name"]].set_info(player)


class TacticsSidebar(ttk.Frame):
    """"""

    parent: MainApplication
    tactic_labels: list
    tactics: list[tk.Button]

    def __init__(self, parent: MainApplication, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.tactic_labels = []

    def load_tactic_labels_list(self):
        if self.parent.dm is None:
            raise ValueError("DataManager not initialized.")
        if self.parent.vm is None:
            raise ValueError("VisualizationManager not initialized.")

        for widget in self.winfo_children():
            widget.destroy()

        input_path = (
            Path.cwd()
#            / "research_project"
            / "tactic_labels"
            / f"{self.parent.dm.get_map_name()}_tactics.json"
        )

        if not input_path.exists():
            print(f"Tactic labels file not found at: {input_path}")
            return

        with open(input_path, "r") as f:
            self.tactic_labels = json.load(f)

        for tactic in self.tactic_labels:
            tk.Button(
                self,
                text=tactic["name"],
                width=24,
                command=lambda tactic_id=tactic["id"]: self.save_frame_tactic(
                    tactic_id
                ),
            ).pack(side="top", fill="y", expand=True)
        tk.Button(
            self,
            text="DELETE TACTIC",
            width=24,
            height=5,
            command=lambda tactic_id=None: self.save_frame_tactic(tactic_id),
        ).pack(pady=0)

    def save_frame_tactic(self, tactic_id=None):
        selection_start = self.parent.timeline_bar.selection_start_frame
        selection_end = self.parent.timeline_bar.selection_end_frame
        if selection_start is None or selection_end is None:
            return

        match_id = self.parent.dm.get_match_id()
        round_index = self.parent.vm.current_round_index
        frame_index = self.parent.vm.current_frame_index

        output_path = (
            Path.cwd()
#            / "research_project"
            / "tactic_labels"
            / f"{self.parent.dm.get_map_name()}"
            / match_id
        )
        output_path.mkdir(parents=True, exist_ok=True)

        output_file = output_path / f"{match_id}_{round_index + 1}.json"

        # Load existing data if the file exists
        if output_file.exists():
            with open(output_file, "r") as f:
                round_tactic_data = json.load(f)
        else:
            round_tactic_data = {}

        # Ensure consistent ordering
        frame_range = range(
            min(selection_start, selection_end), max(selection_start, selection_end) + 1
        )

        if tactic_id is None:
            # Remove tactic entries for these frames
            for frame in frame_range:
                round_tactic_data.pop(str(frame), None)
        else:
            # Assign tactic ID
            for frame in frame_range:
                round_tactic_data[str(frame)] = tactic_id

        # Save json
        with open(output_file, "w") as f:
            json.dump(round_tactic_data, f, indent=4)

        self.parent.timeline_bar._deselect_frames()
        self.parent.timeline_bar.reset_timeline_bar(round_index)
        self.parent.timeline_bar.set_timeline_bar_progress(round_index, frame_index)


class PredictionLabel(ttk.Frame):
    """Displays predicted tactic information."""

    parent: MainApplication
    label: tk.Text
    run_prediction_button: tk.Button

    predictor: Predictor
    predictor_output: list

    def __init__(self, parent: MainApplication, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.predictor = None
        self.predictor_output = []

        self.label = tk.Text(self, font=("Arial", 14), height=1, wrap="none")
        self.run_prediction_button = tk.Button(
            self,
            text="Run Predictor",
            command=lambda tactic_id=None: self.run_predictor(),
            state="disabled",
        )
        self.run_prediction_button.pack(pady=0)

        # Add format tags for styling
        self.label.tag_configure("label", foreground="black", font=("Arial", 12))
        self.label.tag_configure(
            "tactic", foreground="steelblue", font=("Arial", 12, "bold")
        )

        self.label.configure(state=tk.DISABLED)
        self.label.pack(side="top", fill="x", expand=True)
        self.pack(side="top", fill="x")

    def check_graphs(self):
        """Enables the run prediction button if labeled frame data exists."""
        if self.parent.dm is None:
            return

        label_folder = (
            Path.cwd()
#            / "research_project"
            / "graphs"
            / f"{self.parent.dm.get_match_id()}"
        )

        if label_folder.exists() and label_folder.is_dir() and self.predictor is None:
            self.run_prediction_button.configure(state="normal")
        else:
            self.run_prediction_button.configure(state="disabled")

    def get_prediction_for_frame(self, round_index: int, frame_index: int):
        if not self.predictor_output:
            return

        # if round_index < 0 or round_index >= len(self.predictor_output):
        #     return

        # if frame_index < 0 or frame_index >= len(self.predictor_output[round_index]):
        #     return

        predicted_tactic = self.predictor_output[round_index][frame_index]
        self.update_prediction(predicted_tactic)

    def update_prediction(self, tactic_id: str):
        """Updates the label with the predicted tactic name."""
        self.label.configure(state=tk.NORMAL)
        self.label.delete("1.0", tk.END)

        self.label.insert(tk.END, "Predicted tactic: ", "label")
        self.label.insert(tk.END, tactic_id, "tactic")

        self.label.configure(state=tk.DISABLED)

    def clear_prediction(self):
        """Clears the prediction label."""
        self.label.configure(state=tk.NORMAL)
        self.label.delete("1.0", tk.END)
        self.label.configure(state=tk.DISABLED)
        self.predictor = None
        self.predictor_output = None
        self.run_prediction_button.configure(state="disabled")

    def run_predictor(self):
        self.predictor = Predictor(
#            Path.cwd() / "research_project" / "models" / "checkpoint7.pt",
            Path.cwd() / "models" / "checkpoint7.pt",
            Path.cwd()
#            / "research_project"
            / "graphs"
            / f"{self.parent.dm.get_match_id()}",
        )
        # Get raw output (flat list of predictions)
        raw_output = self.predictor.predict()

        # Convert to nested list [round][frame]
        self.predictor_output = self._structure_predictions_by_round(raw_output)

        self.run_prediction_button.configure(state="disabled")

        self.parent.reload_visualization_widgets()
        self.parent.timeline_bar.load_timeline_predictions(
            self.parent.timeline_bar.visualized_round_index
        )

    def _structure_predictions_by_round(self, flat_predictions: list):
        """Convert a flat list of predictions into a nested list: predictions[round][frame]."""
        if self.parent.dm is None:
            raise ValueError("DataManager not initialized.")

        structured = []
        index = 0
        for round_index in range(self.parent.dm.get_round_count()):
            frame_count = self.parent.dm.get_frame_count(round_index)
            round_predictions = flat_predictions[index : index + frame_count]
            structured.append(round_predictions)
            index += frame_count

        return structured
