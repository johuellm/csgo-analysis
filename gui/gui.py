import tkinter
import DataManager
import VisualisationManager
import Routine
from matplotlib.backend_bases import key_press_handler # Implement the default Matplotlib key bindings.
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# Game Data
dm = DataManager.DataManager()
vizm = VisualisationManager.VisualisationManager()
dm.LoadData(r"/mnt/d/dev/csgo-analysis/demos/esta/0013db25-4444-452b-980b-7702dc6fb810.json")
vizm.DrawMap(dm.GetMap())

# UI Components
root = tkinter.Tk()
root.wm_title("CS:GO Analytics")
canvas = FigureCanvasTkAgg(vizm.fig, master=root)  # A tk.DrawingArea.

# UI State
currentRoutine = 0
checkbuttonsPlayers = [tkinter.IntVar(value=1), tkinter.IntVar(value=0), tkinter.IntVar(value=0),
                       tkinter.IntVar(value=0), tkinter.IntVar(value=0)]
checkbuttonShowOpponents = tkinter.IntVar()
fmtPlayers = ['o-b', 'o-g','o-r','o-c','o-m']
fmtOpponents = ['bisque', 'darkorange','orange','wheat','gold']
labelRoundStats = tkinter.StringVar()

# UI Events
canvas.mpl_connect("key_press_event", lambda event: print(f"you pressed {event.key}"))
canvas.mpl_connect("key_press_event", key_press_handler)

def update_canvas():
  global currentRoutine, checkbuttonsPlayers, spinbox_routineLength, spinbox_roundId,checkbuttonShowOpponents

  # retrieve UI values
  showOpponents = checkbuttonShowOpponents.get()
  routineLength = int(spinbox_routineLength.get())
  roundId = int(spinbox_roundId.get())

  # remove old patches and scatters
  for patch in vizm.axes.patches:
    patch.remove()
  for collection in vizm.axes.collections:
    collection.remove()
  for line in vizm.axes.lines:
    line.remove()

  # retrieve routineId
  routines = dm.GetAllTeamRoutines(roundId, routineLength)
  for playerId in range(5):
    if checkbuttonsPlayers[playerId].get() and dm.GetPlayerAlive(playerId, "t", roundId, currentRoutine*routineLength):
      vizm.DrawRoutine(routines[0].GetRoutinesPlayer(playerId)[currentRoutine], fmt=fmtPlayers[playerId])
    if showOpponents  and dm.GetPlayerAlive(playerId, "ct", roundId, currentRoutine*routineLength):
      vizm.DrawRoutine(routines[1].GetRoutinesPlayer(playerId)[currentRoutine], linestyle="-", marker="o", color=fmtOpponents[playerId])

  # update roundStats
  roundStats = dm.GetRoundStats(roundId, currentRoutine*routineLength)
  update_roundstats(roundStats)

  # required to update canvas and attached toolbar!
  print("RoutineId %d" % currentRoutine)
  canvas.draw()

def first_frame():
  global currentRoutine
  currentRoutine = 0
  update_canvas()

def next_frame():
  global currentRoutine, spinbox_routineLength, spinbox_roundId
  roundId = int(spinbox_roundId.get())
  routineLength = int(spinbox_routineLength.get())
  if currentRoutine < len(dm.GetAllTeamRoutines(roundId, routineLength)[0].routines1) - 1:
    currentRoutine = currentRoutine + 1
    update_canvas()

def previous_frame():
  global currentRoutine
  if currentRoutine > 0:
    currentRoutine = currentRoutine - 1
    update_canvas()

def last_frame():
  global currentRoutine, spinbox_routineLength, spinbox_roundId
  roundId = int(spinbox_roundId.get())
  routineLength = int(spinbox_routineLength.get())
  currentRoutine = len(dm.GetAllTeamRoutines(roundId, routineLength)[0].routines1) - 1
  update_canvas()

def update_roundstats(roundstats):
  labelRoundStats.set(("Round Winner %s, Reason: %s\n" % (roundstats.winningSide, roundstats.roundEndReason)) +
             ("Players 1: hp=%d, alive=%s, weapon=%s, equipment=%d\n"
              % (roundstats.players[0].hp, roundstats.players[0].alive, roundstats.players[0].activeWeapon, roundstats.players[0].equipmentValue)) +
             ("Players 2: hp=%d, alive=%s, weapon=%s, equipment=%d\n"
              % (roundstats.players[1].hp, roundstats.players[1].alive, roundstats.players[1].activeWeapon, roundstats.players[1].equipmentValue)) +
             ("Players 3: hp=%d, alive=%s, weapon=%s, equipment=%d\n"
              % (roundstats.players[2].hp, roundstats.players[2].alive, roundstats.players[2].activeWeapon, roundstats.players[2].equipmentValue)) +
             ("Players 4: hp=%d, alive=%s, weapon=%s, equipment=%d\n"
              % (roundstats.players[3].hp, roundstats.players[3].alive, roundstats.players[3].activeWeapon, roundstats.players[3].equipmentValue)) +
             ("Players 5: hp=%d, alive=%s, weapon=%s, equipment=%d\n"
              % (roundstats.players[4].hp, roundstats.players[4].alive, roundstats.players[4].activeWeapon, roundstats.players[4].equipmentValue)) +
             ("Opponents: alivePlayers=%d, equipment=%d")
              % (roundstats.opponentsAlive, roundstats.opponentEquipmentValue))

# UI Layout
# Packing order is important. Widgets are processed sequentially and if there
# is no space left, because the window is too small, they are not displayed.
# The canvas is rather flexible in its size, so we pack it last which makes
# sure the UI controls are displayed as long as possible.
routine_settings_frame = tkinter.Frame(master=root)
players_frame = tkinter.Frame(master=root)
buttons_frame = tkinter.Frame(master=root)
roundstats_frame = tkinter.LabelFrame(master=root, text="Round Stats")
roundstats_frame.pack(side=tkinter.BOTTOM, fill=tkinter.X)
routine_settings_frame.pack(side=tkinter.BOTTOM)
players_frame.pack(side=tkinter.BOTTOM)
buttons_frame.pack(side=tkinter.BOTTOM)

# buttons frame
button_first = tkinter.Button(master=buttons_frame, text="First", command=first_frame)
button_next = tkinter.Button(master=buttons_frame, text="Next", command=next_frame)
button_previous = tkinter.Button(master=buttons_frame, text="Previous", command=previous_frame)
button_last = tkinter.Button(master=buttons_frame, text="Last", command=last_frame)
button_last.pack(side=tkinter.RIGHT)
button_next.pack(side=tkinter.RIGHT)
button_previous.pack(side=tkinter.RIGHT)
button_first.pack(side=tkinter.RIGHT)

# players frame
checkbutton_p5 = tkinter.Checkbutton(master=players_frame, text="Player5", variable=checkbuttonsPlayers[4])
checkbutton_p4 = tkinter.Checkbutton(master=players_frame, text="Player4", variable=checkbuttonsPlayers[3])
checkbutton_p3 = tkinter.Checkbutton(master=players_frame, text="Player3", variable=checkbuttonsPlayers[2])
checkbutton_p2 = tkinter.Checkbutton(master=players_frame, text="Player2", variable=checkbuttonsPlayers[1])
checkbutton_p1 = tkinter.Checkbutton(master=players_frame, text="Player1", variable=checkbuttonsPlayers[0])
checkbutton_p5.pack(side=tkinter.RIGHT)
checkbutton_p4.pack(side=tkinter.RIGHT)
checkbutton_p3.pack(side=tkinter.RIGHT)
checkbutton_p2.pack(side=tkinter.RIGHT)
checkbutton_p1.pack(side=tkinter.RIGHT)

# routine settings frame
spinbox_routineLength = tkinter.Spinbox(master=routine_settings_frame, from_=1, to=20)
spinbox_roundId = tkinter.Spinbox(master=routine_settings_frame, from_=1, to=30)
checkbutton_showOpponents = tkinter.Checkbutton(master=routine_settings_frame, text="Show Opponents", variable=checkbuttonShowOpponents)
checkbutton_showOpponents.pack(side=tkinter.RIGHT)
spinbox_routineLength.pack(side=tkinter.RIGHT)
spinbox_roundId.pack(side=tkinter.RIGHT)

# roundstats frame
label_roundstats = tkinter.Label(master=roundstats_frame, textvariable=labelRoundStats, anchor="nw", justify=tkinter.LEFT)
label_roundstats.pack(fill=tkinter.BOTH, expand=True)


# put everything together
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)

update_canvas()
canvas.draw()

tkinter.mainloop()

