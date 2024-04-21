import functools
from pathlib import Path
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

from models.data_manager import DataManager
from models.visualization_manager import VisualizationManager

from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from awpy.visualization.plot import plot_map

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
        self.parent.vm.draw_round_start(round_index)
        self.canvas.draw()
    
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

        self.parent.vm.progress_visualization()
        self.canvas.draw()
        if self._do_play_visualization:
            self.parent.root.after(500, self._tick_visualization)
    
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
        round_count = 25 if self.parent.dm is None else self.parent.dm.get_round_count()
        button_state = 'disabled' if self.parent.dm is None else 'normal'
        for round_index in range(round_count):
            # Add a button for each round
            round_number = round_index + 1
            round_button = ttk.Button(self, text=f'{round_number}', command=functools.partial(self.parent.canvas.draw_round, round_index), state=button_state)
            round_button.pack(side='left', fill='x', expand=True)
        self.pack(side='top', fill='x')
    
    def update_round_list(self):
        """Updates the list of round buttons."""
        for widget in self.winfo_children():
            widget.destroy()
        self._create_round_buttons()

class TimelineBar(ttk.Frame):
    """A bar that displays a scrubbable timeline with markers for events that happened during the round."""
    parent: MainApplication
    _button: ttk.Button

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
        self._button = play_button
    
    def reload_play_button(self, create_pause_button: bool = False):
        """Reloads the play button."""
        if create_pause_button:
            self._button.configure(text='Pause', command=self.call_pause_visualization)
        else:
            self._button.configure(text='Play', command=self.call_play_visualization, state='disabled' if self.parent.dm is None else 'normal')
    
    def _create_timeline_bar(self, round_index: int | None = None):
        """Creates the timeline bar."""

        timeline_bar = tk.Canvas(self, height=100, bg='white', border=1, borderwidth=1)
        timeline_bar.pack(side='left', fill='x', expand=True)

        # If round_index is None, just create the bar and don't add any event markers
        if round_index is None:
            return

        if self.parent.dm is None:
            raise ValueError('DataManager not initialized.')
        if self.parent.vm is None:
            raise ValueError('VisualizationManager not initialized.')

        raise NotImplementedError
    
    def progress_timeline_bar(self):
        """Progresses the timeline bar by one frame."""
        raise NotImplementedError
