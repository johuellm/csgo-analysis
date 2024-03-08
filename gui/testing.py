import DataManager, VisualisationManager, Routine

if __name__ == "__main__":
  dm = DataManager.DataManager()
  dm.LoadData(r"/mnt/d/dev/csgo-analysis/demos/esta/0013db25-4444-452b-980b-7702dc6fb810.json")

  # testing
  # alive = dm.GetPlayerAlive(1, 16, 271)
  # print("Alive: " + str(alive))

  routine = dm.GetPlayerRoutine(1, 1, 5, 5)
  print(str(routine.x))
  print(str(routine.y))
