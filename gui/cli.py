import DataManager, VisualisationManager, Routine

if __name__ == "__main__":
  dm = DataManager.DataManager()
  vizm = VisualisationManager.VisualisationManager()
  dm.LoadData(r"/mnt/d/dev/csgo-analysis/demos/esta/0013db25-4444-452b-980b-7702dc6fb810.json")

  routines = dm.GetAllTeamRoutines(16, Routine.ROUTINE_LENGTH)
  for id, routine in enumerate(routines[0].routines1):
    print("x%d: %s" % (id, ",".join(map(str,routine.x))))
    print("y%d: %s" % (id, ",".join(map(str,routine.y))))

  vizm.DrawMap(dm.GetMap())
  vizm.DrawRoutine(routines[0].routines1[0])
  vizm.Render()
