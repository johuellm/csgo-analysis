import tkinter as tk
from tkinter import ttk
from awpy.types import PlayerInfo

from models.team_type import TeamType


class PlayerInfoFrame(ttk.Frame):
    # health_bar_canvas: tk.Canvas
    info_label: tk.Text

    def __init__(self, parent: ttk.Frame, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # self.health_bar_canvas = tk.Canvas(self, width=100, height=20)

        self.info_label = tk.Text(self, width=40, height=5)
        self.info_label.pack()

        self.pack()
    
    def set_info(self, player_info: PlayerInfo):
        """Sets the player info to be displayed in the frame."""
        hp = player_info['hp']
        armor = player_info['armor']
        name = player_info['name']
        weapons = [w['weaponName'] for w in player_info['inventory'] or []]
        money = player_info['cash']
        has_bomb = player_info['hasBomb']
        has_defuse = player_info['hasDefuse']

        self.info_label.config(state=tk.NORMAL)
        self.info_label.delete('1.0', tk.END)
        self.info_label.insert(tk.END, f'{name} | HP: {hp} | Armor: {armor}\n')
        self.info_label.insert(tk.END, f'Weapons: {", ".join(weapons)}\n')
        self.info_label.insert(tk.END, f'Money: {money}\n')

        match TeamType.from_str(player_info['side']):
            case TeamType.CT:
                self.info_label.insert(tk.END, f'Has Bomb: {has_bomb}\n')
            case TeamType.T:
                self.info_label.insert(tk.END, f'Has Defuse: {has_defuse}\n')

        self.info_label.config(state=tk.DISABLED)
