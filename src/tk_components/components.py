from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from models.data_manager import DataManager
from models.visualization_manager import VisualizationManager

from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from awpy.visualization.plot import plot_map

class MainApplication(tk.Frame):
    """Parent frame for all non-root components. Must be attached to root."""
    root: tk.Tk
    dm: DataManager | None
    vm: VisualizationManager | None
    top_bar_menu: 'TopBarMenu'
    canvas: 'CanvasPanel'

    def __init__(self, root: tk.Tk, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)
        self.root = root
        self.dm = None
        self.vm = None

        # Create GUI here
        self.top_bar_menu = TopBarMenu(self.root, self)
        self.top_bar_menu.pack(side='top', fill='x')

        self.canvas = CanvasPanel(self, self)
        self.canvas.pack(side='top', fill='both', expand=True)

        self.pack(side='top', fill='both', expand=True)
    
    def exit(self):
        """Exits the application."""
        self.root.quit()
        self.root.destroy()

class TopBarMenu(tk.Frame):
    """Top bar menu for the application. Must be attached to root."""
    root: tk.Tk
    main_app: MainApplication

    def __init__(self, root: tk.Tk, main_app: MainApplication, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)
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
        file_path = Path(filedialog.askopenfilename(title='Select a CS:GO demo file', filetypes=[('JSON files', '*.json'), ('All files', '*.*')]))
        if file_path == ".":
            # User cancelled the file dialog
            return
        self.main_app.dm = DataManager.from_file(file_path, do_validate=False)
        self.main_app.vm = VisualizationManager.from_map(self.main_app.dm.get_map_name())
        self.main_app.canvas.draw_current_map()

class CanvasPanel(tk.Frame):
    """Panel for displaying plots."""
    parent: MainApplication
    canvas: FigureCanvasTkAgg

    def __init__(self, parent: MainApplication, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

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
            raise ValueError('No map loaded in the VisualizationManager.')
        # Remove the current canvas before creating the new one so there aren't two
        self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(self.parent.vm.fig, self)
        self.__prep_canvas_widget()
