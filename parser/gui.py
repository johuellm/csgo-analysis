import logging
import parsing
import plotting
import mathing
import tkinter as tk
from tkinter import filedialog
import os

# Note: This file isn't being worked on anymore. The CLI is easier to work with, so I switched attention to exclusively that.

def get_demo_file_name() -> str:
    """
    Returns the path to the demo file provided by the user
    """
    file_path = filedialog.askopenfilename(title="Open a .dem file",filetypes=[("demo files", "*.dem")])
    return file_path

def get_csv_output_file_name() -> str:
    """
    Returns the path to an output file provided by the user
    """
    file_path = filedialog.asksaveasfilename(title="Choose where to save the .csv file", filetypes=[("csv files", "*.csv")])
    if file_path.endswith(".csv") is False:
        file_path += ".csv"
    return file_path

def get_gif_output_directory() -> str:
    """
    Returns the path to an output directory provided by the user
    """
    file_path = filedialog.askdirectory(initialdir=os.getcwd(), title="Choose where you want the .gif files to be saved:")
    # TODO: Handle cases where user doesn't enter anything
    return file_path

# Taken from https://stackoverflow.com/questions/3352918/how-to-center-a-window-on-the-screen-in-tkinter
def center(win):
    """
    centers a tkinter window
    :param win: the main window or Toplevel window to center
    """
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()

def run() -> None:
    """
    Run through the entire process of asking player for a demo file, extracting info from it, and saving it as a .csv.
    """

    try:
        logging.debug("Asking user for demo file name\n")
        input_file_path = get_demo_file_name()
        if input_file_path == "":
            return
        logging.debug("Got demo file name: " + input_file_path + "\n")
        logging.debug("Parsing demo file\n")
        parsed_demo_data = parsing.parse_demo_file(input_file_path)
        logging.debug("Parsed demo file\n")
        logging.debug("Extracting player information\n")
        player_information = parsing.extract_player_information(parsed_demo_data)
        logging.debug("Extracted player information\n")
        logging.debug("Asking user for output file name\n")
        output_file_path = get_csv_output_file_name()
        logging.debug("Got output file name: " + output_file_path + "\n")
        logging.debug("Writing player information to output file\n")
        parsing.write_player_information_to_csv(player_information, output_file_path)
        logging.debug("Wrote player information to output file\n")
        logging.debug("Done\n")
        logging.debug("----------------------------------------------------\n")
    except Exception as error:
        logging.error(f"ERROR: {str(error)}\n")

def main():
    """
    """
    logging.basicConfig(filename="debug.log", encoding="utf-8", level=logging.DEBUG)

    window = tk.Tk()
    window.wm_title("CS:GO Demo File Player Data Extractor")
    # Commenting this out to see if it stops raising an issue with certain anti-virus software
    # window.wm_iconbitmap("csgo.ico")
    window.geometry("450x250")
    open_file_button = tk.Button(
        window,
        text = "Extract Data from .dem File\n(opens a file dialog)",
        bd = 10,
        bg = "grey",
        fg = "white",
        font = "Helvetica",
        height = 2,
        command = run,
        padx = 10,
        pady = 10,
        relief = "groove",
    )
    open_file_button.pack(fill=tk.BOTH, side=tk.LEFT, expand=tk.YES)
    center(window)
    window.mainloop()

if __name__ == "__main__":
    main()
    