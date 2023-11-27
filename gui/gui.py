import json
import tkinter

# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)

from awpy.visualization.plot import plot_frame_map_control

# Awpy plots
with open(r"/mnt/d/dev/csgo-analysis/csgoml/demos/dust2/00e7fec9-cee0-430f-80f4-6b50443ceacd.json") as fp:
  data = json.load(fp)
maxFrames = len(data['gameRounds'][16]['frames']) - 1
currentFrame = 0
fig, axes = plot_frame_map_control(data['mapName'], data['gameRounds'][16]['frames'][currentFrame], plot_type='players')

# UI Components
root = tkinter.Tk()
root.wm_title("Embedding in Tk")
canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
# pack_toolbar=False will make it easier to use a layout manager later on.
toolbar = NavigationToolbar2Tk(canvas, root, pack_toolbar=False)

# UI Events
canvas.mpl_connect(
  "key_press_event", lambda event: print(f"you pressed {event.key}"))
canvas.mpl_connect("key_press_event", key_press_handler)




def update_frame(newFrame):
  global currentFrame, fig, axes

  # retrieve frame
  currentFrame = int(newFrame)
  frame = data['gameRounds'][16]['frames'][currentFrame]

  # remove old patches and scatters
  for patch in axes.patches:
    patch.remove()
  for collection in axes.collections:
    collection.remove()

  fig, axes = plot_frame_map_control(data['mapName'], frame, plot_type='players', given_fig_ax=(fig, axes))

  # required to update canvas and attached toolbar!
  print("New Frame %s" % newFrame)
  canvas.draw()

def next_frame():
  global currentFrame, fig, axes
  if currentFrame < maxFrames:
    update_frame(currentFrame + 1)

def previous_frame():
  global currentFrame, fig, axes
  if currentFrame > 0:
    update_frame(currentFrame - 1)

slider_update = tkinter.Scale(root, from_=1, to=maxFrames, orient=tkinter.HORIZONTAL,
                              command=update_frame, label="Current Frame")

# UI Layout
# Packing order is important. Widgets are processed sequentially and if there
# is no space left, because the window is too small, they are not displayed.
# The canvas is rather flexible in its size, so we pack it last which makes
# sure the UI controls are displayed as long as possible.
button_quit = tkinter.Button(master=root, text="Quit", command=root.destroy)
button_next = tkinter.Button(master=root, text="Next", command=next_frame)
button_previous = tkinter.Button(master=root, text="Previous", command=previous_frame)
button_previous.pack(side=tkinter.BOTTOM)
button_quit.pack(side=tkinter.BOTTOM)
button_next.pack(side=tkinter.BOTTOM)
slider_update.pack(side=tkinter.BOTTOM)
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)

toolbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
toolbar.update()
canvas.draw()

tkinter.mainloop()
