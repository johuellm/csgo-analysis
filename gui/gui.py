# import tkinter
import numpy as np
import pandas as pd
import awpy

from awpy.visualization.plot import plot_map, position_transform
from awpy.data import NAV
from matplotlib import patches
import matplotlib.pyplot as plt

NAV["de_dust2"][152]
f, ax = plot_map(map_name="de_dust2", map_type='simpleradar', dark=True)

for a in NAV["de_dust2"]:
    area = NAV["de_dust2"][a]
    area["southEastX"] = position_transform("de_dust2", area["southEastX"], "x")
    area["northWestX"] = position_transform("de_dust2", area["northWestX"], "x")
    area["southEastY"] = position_transform("de_dust2", area["southEastY"], "y")
    area["northWestY"] = position_transform("de_dust2", area["northWestY"], "y")
    width = (area["southEastX"] - area["northWestX"])
    height = (area["northWestY"] - area["southEastY"])
    southwest_x = area["northWestX"]
    southwest_y = area["southEastY"]
    rect = patches.Rectangle((southwest_x,southwest_y), width, height, linewidth=1, edgecolor="yellow", facecolor="None")
    ax.add_patch(rect)

plt.show()

# data_excel = pd.read_excel('2023-05-09-sheet-data.xlsx')
# print(data_excel)



























# # Implement the default Matplotlib key bindings.
# from matplotlib.backend_bases import key_press_handler
# from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
#                                                NavigationToolbar2Tk)
# from matplotlib.figure import Figure


# root = tkinter.Tk()
# root.wm_title("Embedding in Tk")

# fig = Figure(figsize=(5, 4), dpi=100)
# t = np.arange(0, 3, .01)
# ax = fig.add_subplot()
# line, = ax.plot(t, 2 * np.sin(2 * np.pi * t))
# ax.set_xlabel("time [s]")
# ax.set_ylabel("f(t)")

# canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
# canvas.draw()

# # pack_toolbar=False will make it easier to use a layout manager later on.
# toolbar = NavigationToolbar2Tk(canvas, root, pack_toolbar=False)
# toolbar.update()

# canvas.mpl_connect(
#     "key_press_event", lambda event: print(f"you pressed {event.key}"))
# canvas.mpl_connect("key_press_event", key_press_handler)

# button_quit = tkinter.Button(master=root, text="Quit", command=root.destroy)


# def update_frequency(new_val):
#     # retrieve frequency
#     f = float(new_val)

#     # update data
#     y = 2 * np.sin(2 * np.pi * f * t)
#     line.set_data(t, y)

#     # required to update canvas and attached toolbar!
#     canvas.draw()


# slider_update = tkinter.Scale(root, from_=1, to=5, orient=tkinter.HORIZONTAL,
#                               command=update_frequency, label="Frequency [Hz]")

# # Packing order is important. Widgets are processed sequentially and if there
# # is no space left, because the window is too small, they are not displayed.
# # The canvas is rather flexible in its size, so we pack it last which makes
# # sure the UI controls are displayed as long as possible.
# button_quit.pack(side=tkinter.BOTTOM)
# slider_update.pack(side=tkinter.BOTTOM)
# toolbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
# canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)

# tkinter.mainloop()

