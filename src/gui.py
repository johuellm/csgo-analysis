import tkinter as tk

from tk_components.components import MainApplication

# Time to design a GUI? # TODO.

def main():
    root = tk.Tk()
    root.title("CS:GO Demo Visualizer")
    root.geometry("1920x1080")
    MainApplication(root).pack(side='top', fill='both', expand=True)
    # Exit the application when the window is closed
    # This is required because, for some reason, the initial instantiation of the FigureCanvasTkAgg prevents the script from terminating even after the window is closed.
    # If this canvas is ever destroyed and re-created (e.g. when a new file is loaded), the script will terminate as expected.
    # To prevent issues in that initial case, this manual exit bind is added.
    # See: https://stackoverflow.com/a/67663998
    root.protocol("WM_DELETE_WINDOW", lambda: MainApplication(root).exit())
    root.mainloop()

if __name__ == '__main__':
    main()