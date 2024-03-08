import DataManager, VisualisationManager, Routine, RoundStats

if __name__ == "__main__":
  dm = DataManager.DataManager()
  dm.LoadData(r"/mnt/d/dev/csgo-analysis/demos/esta/0013db25-4444-452b-980b-7702dc6fb810.json")

  # testing
  dm.GetAllTeamRoutines(15, 1)  # for initializing everything
  roundStats = dm.GetRoundStats(15, 35)
  print(roundStats.winningSide)
  print(roundStats.roundEndReason)
  print(roundStats.opponentsAlive)
  print(roundStats.opponentEquipmentValue)
  print(roundStats.clocktime)
  for p in roundStats.players:
    print("%s,%s,%s,%s" % (p.activeWeapon, str(p.equipmentValue), str(p.hp), str(p.alive)))
