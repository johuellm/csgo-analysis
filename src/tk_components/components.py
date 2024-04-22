import functools
from pathlib import Path
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

from models.data_manager import DataManager
from models.team_type import TeamType
from models.visualization_manager import VisualizationManager

from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from awpy.visualization.plot import plot_map

from tk_components.imports import CanvasTooltip

class MainApplication(ttk.Frame):
    """Parent frame for all non-root components. Must be attached to root."""
    root: tk.Tk
    dm: DataManager | None
    vm: VisualizationManager | None
    top_bar_menu: 'TopBarMenu'
    canvas: 'CanvasPanel'
    round_select_bar: 'RoundSelectBar'
    timeline_bar: 'TimelineBar'

    def __init__(self, root: tk.Tk, *args, **kwargs):
        ttk.Frame.__init__(self, root, *args, **kwargs)
        self.root = root
        self.dm = None
        self.vm = None

        # Create GUI here
        self.top_bar_menu = TopBarMenu(self.root, self)
        self.top_bar_menu.pack(side='top', fill='x')

        self.canvas = CanvasPanel(self)
        self.canvas.pack(side='top', fill='both', expand=True)

        self.timeline_bar = TimelineBar(self)
        self.timeline_bar.pack(side='bottom', fill='x')
        
        self.round_select_bar = RoundSelectBar(self)
        self.round_select_bar.pack(side='bottom', fill='x')

        self.pack(side='top', fill='both', expand=True)
    
    def load_file_and_reload(self, file_path: Path):
        """Re-initializes the DataManager, VisualizationManager, and relevant components after a new file is loaded."""
        self.dm = DataManager.from_file(file_path, do_validate=False)
        self.vm = VisualizationManager.from_data_manager(self.dm)
        self.canvas.draw_current_map()
        self.round_select_bar.update_round_list()
        self.timeline_bar.reload_play_button()
        self.timeline_bar.reset_timeline_bar()
    
    def exit(self):
        """Exits the application."""
        self.root.quit()
        self.root.destroy()

class TopBarMenu(ttk.Frame):
    """Top bar menu for the application. Must be attached to root."""
    root: tk.Tk
    main_app: MainApplication

    def __init__(self, root: tk.Tk, main_app: MainApplication, *args, **kwargs):
        ttk.Frame.__init__(self, root, *args, **kwargs)
        self.root = root
        self.main_app = main_app

        # Create GUI here

        # Create top bar
        top_bar = tk.Menu(self.root)
        self.root.config(menu=top_bar)

        # Create File menu
        file_menu = tk.Menu(top_bar, tearoff=0)
        top_bar.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='Open', command=self.open_demo_file)
        file_menu.add_command(label='Exit', command=self.main_app.exit)

        self.pack(side='top', fill='x')
    
    def open_demo_file(self):
        """Prompts user to select a .json file (ideally, this is the .json file corresponding to a CS:GO demo) and updates the main application's DataManager and VisualizationManager."""
        file_dialog_response = filedialog.askopenfilename(title='Select a CS:GO demo file', filetypes=[('JSON files', '*.json'), ('All files', '*.*')])
        if file_dialog_response == "":
            # User cancelled the file dialog
            return
        file_path = Path(file_dialog_response)
        self.main_app.load_file_and_reload(file_path) 

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
        default_figure, _ = plot_map(map_type='simpleradar')
        self.canvas = FigureCanvasTkAgg(default_figure, self) # Note: this instantiation is problematic - see the comment in main() in src/gui.py. Figure out a way to fix this at some point.
        self.__prep_canvas_widget()

        self.pack(side='top', fill='both', expand=True)

    def __prep_canvas_widget(self):
        """Adds key press functionality and packs the canvas widget."""
        self.canvas.mpl_connect('key_press_event', lambda event: key_press_handler(event, self.canvas))
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side='top', fill='both', expand=True)
    
    def draw_current_map(self):
        """Ensures there is a map loaded in the VisualizationManager and then draws it."""
        if self.parent.vm is None:
            raise ValueError('VisualizationManager not initialized.')
        # Remove the current canvas before creating the new one so there aren't two
        self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(self.parent.vm.fig, self)
        self.__prep_canvas_widget()
    
    def draw_round(self, round_index: int):
        """Draws the map at the start of the given round number."""
        if self.parent.dm is None:
            raise ValueError('DataManager not initialized.')
        if self.parent.vm is None:
            raise ValueError('VisualizationManager not initialized.')
        
        # Draw on map canvas
        self.parent.vm.draw_round_start(round_index)
        self.canvas.draw()

        # Reset timeline bar
        self.parent.timeline_bar.reset_timeline_bar(round_index)
    
    def play_visualization(self):
        """Plays the visualization."""
        if self.parent.dm is None:
            raise ValueError('DataManager not initialized.')
        if self.parent.vm is None:
            raise ValueError('VisualizationManager not initialized.')
        
        self._do_play_visualization = True
        self._tick_visualization()
    
    def _tick_visualization(self):
        """Progresses the visualization by one frame."""
        if self.parent.dm is None:
            raise ValueError('DataManager not initialized.')
        if self.parent.vm is None:
            raise ValueError('VisualizationManager not initialized.')

        # Draw on map canvas
        self.parent.vm.progress_visualization()
        self.canvas.draw()

        # Progress timeline bar
        self.parent.timeline_bar.progress_timeline_bar(self.parent.vm.current_round_index, self.parent.vm.current_frame_index)

        if self._do_play_visualization:
            self.parent.root.after(50, self._tick_visualization)
    
    def pause_visualization(self):
        """Pauses the visualization."""
        self._do_play_visualization = False

# TODO: Re-create more Noesis functionality.
# DONE 1. A bar on the bottom that has a list of round numbers. Selecting a round number shows the start of that round on the plot.
# 2. A bar on the right that has a list of players. Each entry has their hp, armor, name, weapon, money, utility, and secondary. The HP is also visualized as a a bar (colored with the team color) that is filled in proportion to the player's HP.
# 3. A bar below the round-select bar, a scrubbable timeline that has markers for events that happened during the round. To the left of this bar is the pause/play button.

class RoundSelectBar(ttk.Frame):
    """A bar that displays a list of the round numbers from the selected demo. Selecting a round number shows the start of that round on the plot."""
    parent: MainApplication

    def __init__(self, parent: MainApplication, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        # Create GUI here
        self._create_round_buttons()

        self.pack(side='top', fill='x')
    
    def _create_round_buttons(self):
        """Creates buttons for each round in the selected demo. If no demo is selected, creates a dummy set of 25 disabled buttons."""
        round_count = 31 if self.parent.dm is None else self.parent.dm.get_round_count()
        button_state = 'disabled' if self.parent.dm is None else 'normal'
        for round_index in range(round_count):
            # Add a button for each round
            round_number = round_index + 1
            # If interested in using ttk.Button here, note that a row of the tk.Buttons, when resized to be smaller, will shrink all buttons equally until reaching a minimum size. After that, then higher round number buttons will be hidden.
            # With the new ttk.Buttons, the higher round number buttons will be hidden immediately, i.e. there is no attempt to shrink all buttons equally.
            # Fix this resizing issue if interested in using ttk.Buttons.
            round_button = tk.Button(self, text=f'{round_number}', command=functools.partial(self.parent.canvas.draw_round, round_index), state=button_state)
            round_button.pack(side='left', fill='x', expand=True)
    
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

        # Create GUI here

        # Play button
        self._create_play_button()

        # Timeline bar
        self._create_timeline_bar()

        self.pack(side='top', fill='x')
    
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
        play_button = ttk.Button(self, text='Play', command=self.call_play_visualization, state='disabled' if self.parent.dm is None else 'normal')
        play_button.pack(side='left', fill='y')
        self._play_pause_button = play_button
    
    def reload_play_button(self, create_pause_button: bool = False):
        """Reloads the play button. If `create_pause_button` is True, creates a pause button instead of a play button."""
        if create_pause_button:
            self._play_pause_button.configure(text='Pause', command=self.call_pause_visualization)
        else:
            self._play_pause_button.configure(text='Play', command=self.call_play_visualization, state='disabled' if self.parent.dm is None else 'normal')

    def _create_timeline_bar(self, round_index: int | None = None):
        """Creates the timeline bar."""

        timeline_canvas = tk.Canvas(self, height=100, bg='white', border=0, borderwidth=0)
        self._timeline_canvas = timeline_canvas
        timeline_canvas.pack(side='left', fill='x', expand=True)

        # Add scrubbing functionality
        timeline_canvas.bind('<Button-1>', self._jump_to_frame) # A single click of Mouse 1
        timeline_canvas.bind('<B1-Motion>', self._jump_to_frame) # Holding Mouse 1 down and dragging

        self.visualized_round_index = round_index

        if round_index is not None:
            self._add_event_markers(round_index)
    
    def _get_pixels_per_frame(self, round_index: int):
        """Returns the number of horizontal pixels in the timeline bar canvas allocated to each frame in round specified by `round_index`."""
        if self.parent.dm is None:
            raise ValueError('DataManager not initialized.')

        total_frames_in_round = self.parent.dm.get_frame_count(round_index)
        canvas_width = self._timeline_canvas.winfo_width()
        return canvas_width / total_frames_in_round
    
    def _jump_to_frame(self, event: tk.Event):
        """Sets the current frame of the visualization to the frame that corresponds to the point clicked on in the timeline bar. Doesn't do anything if no demo is loaded."""
        if self.parent.dm is None:
            return
        if self.parent.vm is None:
            return
        if self.visualized_round_index is None:
            return
        
        # Calculate which frame corresponds to the x-coordinate of the click
        clicked_frame_index = int(event.x / self._get_pixels_per_frame(self.visualized_round_index))

        # Jump to that frame in the visualization
        self.parent.vm.current_frame_index = clicked_frame_index - 1 # -1 because calling progress_visualization() will increment the frame index before updating the plot
        self.parent.vm.progress_visualization()
        self.parent.canvas.canvas.draw()
        self._draw_progress_bar_fill_rectangle(event.x)
    
    def _add_event_markers(self, round_index: int):
        """Adds markers to the timeline bar for each event that happened during the round specified by `round_index`."""
        if self.parent.dm is None:
            raise ValueError('DataManager not initialized.')
        if self.parent.vm is None:
            raise ValueError('VisualizationManager not initialized.')
        
        round_events = self.parent.dm.get_round_events(round_index)
        round_starting_tick = self.parent.dm.get_round_start_tick(round_index)
        pixels_per_tick = self._timeline_canvas.winfo_width() / self.parent.dm.get_round_tick_length(round_index)

        kill_event_color: dict[TeamType, str] = {TeamType.T: 'goldenrod', TeamType.CT: 'darkblue'}

        # Only drawing kill + bomb events for now
        for event in round_events.kills:
            victim_team = TeamType.from_str(event['victimSide'] or "")
            x = int((event['tick'] - round_starting_tick) * pixels_per_tick)
            kill_event_marker = self._timeline_canvas.create_line(x, 0, x, self._timeline_canvas.winfo_height(), fill=kill_event_color[victim_team], tags='kill-event', width=2, activewidth=3)
            tooltip_text = f'{event["attackerName"]} killed {event["victimName"]} with {event["weapon"]}'
            CanvasTooltip(self._timeline_canvas, kill_event_marker, text=tooltip_text) 

        for event in round_events.bomb_events:
            x = int((event['tick'] - round_starting_tick) * pixels_per_tick)
            bomb_event_marker = self._timeline_canvas.create_line(x, 0, x, self._timeline_canvas.winfo_height(), fill='red', tags='bomb-event', width=2, activewidth=3)
            tooltip_text = f'Bomb action {event["bombAction"]} by {event["playerName"]}'
            CanvasTooltip(self._timeline_canvas, bomb_event_marker, text=tooltip_text)

        self._timeline_canvas.update()
    
    def reset_timeline_bar(self, round_index: int | None = None):
        """Resets the timeline bar to its default state. If `round_index` is not None, adds event markers for the round specified by `round_index`."""
        self._timeline_canvas.delete('all')
        self._timeline_canvas.update()
        if round_index is not None:
            self._add_event_markers(round_index)
    
    def _draw_progress_bar_fill_rectangle(self, x: int):
        """Draws a rectangle in the progress bar starting from the left and ending at the x-coordinate specified by `x`."""
        self._timeline_canvas.delete('progress')
        self._timeline_canvas.create_rectangle(0, 0, x, self._timeline_canvas.winfo_height(), fill='gray', tags='progress')
        self._timeline_canvas.tag_lower('progress') # Lower the progress bar along the z-axis so that it doesn't cover the event markers
    
    def progress_timeline_bar(self, round_index: int, current_frame_index: int = 0):
        """Progresses the timeline bar by one frame, calculating how far the bar needs to visually progress by calculating how many ticks happened in the round specified by `round_index`."""
        if self.parent.dm is None:
            raise ValueError('DataManager not initialized.')
        if self.parent.vm is None:
            raise ValueError('VisualizationManager not initialized.')
        
        # Check if the visualized round has changed, as this will require a reset of the timeline bar
        if self.visualized_round_index != round_index:
            self.visualized_round_index = round_index
            self.reset_timeline_bar()
            self._add_event_markers(round_index)

        # Paint the canvas up to current_frame_index * pixels_per_tick in dark gray to indicate progress
        progress_bar_fill_length = int(current_frame_index * self._get_pixels_per_frame(round_index))
        self._draw_progress_bar_fill_rectangle(progress_bar_fill_length)
        self._timeline_canvas.update()
