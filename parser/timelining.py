from dataclasses import dataclass, field
from enum import Enum
import models
import numpy as np

@dataclass
class Position:
    """
    Coordinates
    """
    x: float
    y: float
    z: float

    def __str__(self) -> str:
        return f"({self.x}, {self.y}, {self.z})"

@dataclass
class View:
    """
    Where a player is looking
    """
    x: float # degrees above/below horizon (straight down is 90, straight up is 270)
    y: float # degrees left/right (looking straight east is 0, north is 90, west is 180, south is 270)

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

@dataclass
class Side(Enum):
    """
    The two sides in a CS:GO game
    """
    CT = "Counter-Terrorist"
    T = "Terrorist"

    @staticmethod
    def from_acronym(string: str) -> "Side":
        """
        Returns a Side value for the acronym provided
        """
        if string is None:
            return None
        if string.upper() not in ["CT", "T"]:
            raise ValueError(f"The provided side string {string.upper()} is not one of the two options (CT or T)")
        if string.upper() == "CT":
            return Side.CT
        elif string.upper() == "T":
            return Side.T
    
    @staticmethod
    def invert(side: "Side") -> "Side":
        """
        Returns a Side value opposite to the one provided
        """
        if side == Side.CT:
            return Side.T
        elif side == Side.T:
            return Side.CT
        else:
            raise ValueError(f"The provided side {side} is not one of the two options (Side.CT or Side.T)")

    @staticmethod
    def from_bomb_action(bomb_action: str) -> "Side":
        if "plant" in bomb_action:
            return Side.T
        elif "defuse" in bomb_action:
            return Side.CT
        else:
            raise ValueError(f"The provided bomb action {bomb_action} is not one of the two options (plant or defuse)")

    def __str__(self) -> str:
        return self.name

@dataclass
class Player:
    steam_id: int
    team: str
    side: Side
    name: str

    def __str__(self) -> str:
        return f"{self.team} {self.side} {self.name}"

@dataclass
class PositionedPlayer(Player):
    """
    A player for which we know their position
    """
    position: Position

    def __str__(self) -> str:
        return f"{self.team} {self.side} {self.name} at {self.position}"

@dataclass
class PositionedPlayerWithView(PositionedPlayer):
    """
    A player for which we know their position and view
    """
    view: View

    def __str__(self) -> str:
        return f"{self.team} {self.side} {self.name} at {self.position} looking at {self.view}"

@dataclass
class Event:
    tick: int
    seconds: float
    clock_time: str
    # TODO: Add more stuff here as necessary,
    
    def __str__(self) -> str:
        return f"{self.tick} {self.seconds} {self.clock_time}"

    pass

@dataclass
class PlayerConnectionEvent():
    """
    When a player joins the server
    Note: Does not inherit from Event because it does not have seconds or clock_time
    """
    tick: int
    steam_id: int # Maybe replace this with Player if desired, but each PlayerConnection object only has a steamID in it so maybe not
    action: str

    def __str__(self) -> str:
        return f"Player with ID {self.steam_id} took server action {self.action}"

@dataclass
class Weapon:
    name: str
    weapon_class: str
    ammo_in_magazine: int | None
    ammo_in_reserve: int | None

    def __str__(self) -> str:
        return f"{self.name} ({self.weapon_class}) with {self.ammo_in_magazine} rounds in magazine and {self.ammo_in_reserve} rounds in reserve"

@dataclass
class KillEvent(Event):
    """
    When a player kills another player
    """
    attacker: PositionedPlayerWithView
    victim: PositionedPlayerWithView
    assister: Player | None
    is_suicide: bool
    is_teamkill: bool
    is_wallbang: bool
    penetrated_objects: int
    is_first_kill: bool
    is_headshot: bool
    is_victim_blinded: bool
    is_attacker_blinded: bool
    flash_thrower: Player | None
    is_no_scope: bool
    is_through_smoke: bool
    distance: float
    # is_trade: bool # Can just check if player_traded is None or not
    player_traded: Player | None
    weapon: Weapon

    def __str__(self) -> str:
        attacker_string: str = f"{self.attacker}"
        if self.is_attacker_blinded:
            attacker_string += f" (BLINDED BY {self.flash_thrower})"

        victim_string: str = f"{self.victim}"
        if self.is_victim_blinded:
            victim_string += f" (BLINDED BY {self.flash_thrower})"

        string = f"{attacker_string} killed {victim_string} with {self.weapon} at a distance of {self.distance}"

        # if self.is_headshot:
        #     string += " (HEADSHOT)"
        # if self.is_wallbang:
        #     string += f" (WALLBANG through {self.penetrated_objects} OBJECTS)"
        # if self.is_teamkill:
        #     string += " (TEAMKILL)"
        # if self.is_first_kill:
        #     string += " (FIRST KILL OF ROUND)"
        # if self.is_no_scope:
        #     string += " (NO SCOPE)"
        # if self.is_through_smoke:
        #     string += " (THROUGH SMOKE)"
        # if self.player_traded is not None:
        #     string += f" (TRADED FOR {self.player_traded})"

        string += " (HEADSHOT)" * self.is_headshot
        string += f" (WALLBANG through {self.penetrated_objects} OBJECTS)" * self.is_wallbang
        string += " (TEAMKILL)" * self.is_teamkill
        string += " (FIRST KILL OF ROUND)" * self.is_first_kill
        string += " (NO SCOPE)" * self.is_no_scope
        string += " (THROUGH SMOKE)" * self.is_through_smoke
        string += f" (TRADED FOR {self.player_traded})" * (self.player_traded is not None)

        return string

@dataclass
class DamageEvent(Event):
    """
    When a player takes damage (not sure if only from another player TODO figure this out)
    """
    attacker: PositionedPlayerWithView
    is_attacker_strafe: bool # I don't entirely know what this refers to so maybe it should be did_attacker_strafe ?
    victim: PositionedPlayerWithView
    weapon: Weapon
    hp_damage: int
    hp_damage_taken: int
    armor_damage: int
    armor_damage_taken: int
    hit_group: str
    is_friendly_fire: bool
    distance: float
    zoom_level: int

    def __str__(self) -> str:
        attacker_string: str = f"{self.attacker}"
        attacker_string += " (STRAFING)" * self.is_attacker_strafe
        # TODO Remove these exceptions if it turns out that the values can actually be different
        if self.hp_damage != self.hp_damage_taken:
            raise Exception("hp_damage and hp_damage_taken are not the same")
        if self.armor_damage != self.armor_damage_taken:
            raise Exception("armor_damage and armor_damage_taken are not the same")
        string = f"{attacker_string} damaged {self.victim} for {self.hp_damage_taken}HP and {self.armor_damage_taken}Armor ({self.hp_damage}/{self.armor_damage} raw)"
        string += f" in the {self.hit_group} at a distance of {self.distance} at zoom level {self.zoom_level}"
        string += " (FRIENDLY FIRE)" * self.is_friendly_fire

        return string

@dataclass
class GrenadeThrowEvent(Event):
    """
    When a grenade is thrown
    """
    entity_id: int
    grenade_type: str
    thrower: PositionedPlayer # Grenade throw originating position is in thrower.position

    def __str__(self) -> str:
        return f"{self.thrower} threw a {self.grenade_type} (ID: {self.entity_id})"

@dataclass
class GrenadeTriggerEvent(Event):
    """
    When a grenade "triggers" (i.e. explodes)
    """
    entity_id: int
    grenade_type: str
    position: Position

    def __str__(self) -> str:
        return f"A {self.grenade_type} triggered at {self.position} (ID: {self.entity_id})"

@dataclass
class BombEvent(Event):
    player: PositionedPlayer
    bomb_action: str # i.e. "plant_begin", "plant_abort"
    bomb_site: str # i.e. "A"

    def __str__(self) -> str:
        return f"{self.player} took the action {self.bomb_action} at site {self.bomb_site}"

@dataclass
class WeaponFireEvent(Event):
    player: PositionedPlayerWithView
    is_player_strafe: bool
    weapon: Weapon
    zoom_level: int

    def __str__(self) -> str:
        player_string: str = f"{self.player}"
        player_string += " (STRAFING)" * self.is_player_strafe
        return f"{player_string} fired {self.weapon} at zoom level {self.zoom_level}"

@dataclass
class FlashEvent(Event):
    attacker: PositionedPlayerWithView
    player: PositionedPlayerWithView
    flash_duration: float

    def __str__(self) -> str:
        return f"{self.attacker} flashed {self.player} for {self.flash_duration} seconds"

@dataclass
class PlayerMovementEvent(Event):
    """
    # TODO
    (this one is complicated but this would include ducking, unducking, turning around (?), etc.)
    """
    player: PositionedPlayerWithView

    def __str__(self) -> str:
        raise NotImplementedError("The base PlayerMovementEvent class is not implemented - this shouldn't have happened.")

@dataclass
class StoppingMovingEvent(PlayerMovementEvent):
    """
    When a player stops moving
    """

    def __str__(self) -> str:
        return f"{self.player} stopped moving"

@dataclass
class StartingMovingEvent(PlayerMovementEvent):
    """
    When a player starts moving
    """

    def __str__(self) -> str:
        return f"{self.player} started moving"

@dataclass
class DirectionChangeEvent(PlayerMovementEvent):
    """
    When a player changes direction by a significant amount
    """
    old_velocity: tuple[float, float, float]
    new_velocity: tuple[float, float, float]

    def __str__(self) -> str:
        return f"{self.player} significantly changed movement direction from {self.old_velocity} to {self.new_velocity}"

@dataclass
class SlowedSpeedEvent(PlayerMovementEvent):
    """
    When a player slows their movement speed by a significant amount
    """
    old_speed: float
    new_speed: float

    def __str__(self) -> str:
        return f"{self.player} significantly slowed their speed from {self.old_speed} to {self.new_speed}"

@dataclass
class ReloadStartEvent(Event):
    """
    When a player starts to reload
    """
    player: PositionedPlayerWithView
    weapon: Weapon

    def __str__(self) -> str:
        return f"{self.player} started reloading their {self.weapon}"

@dataclass
class ReloadFinishEvent(Event):
    """
    When a player finishes reloading
    """
    player: PositionedPlayerWithView
    weapon: Weapon

    def __str__(self) -> str:
        return f"{self.player} finished reloading their {self.weapon}"

@dataclass
class ReloadCancelEvent(Event):
    """
    When a player cancels reloading
    """
    player: PositionedPlayerWithView
    weapon: Weapon

    def __str__(self) -> str:
        return f"{self.player} cancelled reloading their {self.weapon}"

@dataclass
class ScopeEvent(Event):
    """
    When a player scopes
    """
    player: PositionedPlayerWithView
    weapon: Weapon

    def __str__(self) -> str:
        return f"{self.player} scoped their {self.weapon}"

@dataclass
class UnscopeEvent(Event):
    """
    When a player unscopes
    """
    player: PositionedPlayerWithView
    weapon: Weapon

    def __str__(self) -> str:
        return f"{self.player} unscoped their {self.weapon}"

@dataclass
class WeaponSwitchEvent(Event):
    """
    When a player's equipped weapon changes
    This assumes that the first entry in the player's 
    inventory list is the currently equipped weapon
    """
    player: PositionedPlayer
    previous_weapon: Weapon
    new_weapon: Weapon

    def __str__(self) -> str:
        return f"{self.player} switched their weapon from {self.previous_weapon} to {self.new_weapon}"

@dataclass
class InventoryChangeEvent(Event):
    """
    When a player's inventory changes
    Note: (a player firing their gun changes their inventory as a weapon with 1 less bullet in the magazine counts as a new gun)
    """
    player: PositionedPlayer
    old_inventory: list[Weapon]
    updated_inventory: list[Weapon]

    def get_inventory_difference(self) -> dict[str, list[Weapon]]:
        return {
            "gained": [weapon for weapon in self.updated_inventory if weapon not in self.old_inventory],
            "lost": [weapon for weapon in self.old_inventory if weapon not in self.updated_inventory],
        }

    def __str__(self) -> str:
        difference: dict[str, list[Weapon]] = self.get_inventory_difference()
        if len(difference["gained"]) > 0 and len(difference["lost"]) > 0:
            return f"{self.player} gained {[str(w) for w in difference['gained']]} and lost {[str(w) for w in difference['lost']]}"
        elif len(difference["gained"]) > 0:
            return f"{self.player} gained {[str(w) for w in difference['gained']]}"
        elif len(difference["lost"]) > 0:
            return f"{self.player} lost {[str(w) for w in difference['lost']]}"
        error_message: str = "InventoryChangeEvent has no difference yet an event was created. This shouldn't have happened."
        error_message += f"\nOld inventory: {self.old_inventory}"
        error_message += f"\nUpdated inventory: {self.updated_inventory}"
        raise Exception(error_message)

# @dataclass
# class BuyEvent(Event):
#     """
#     (what each player (or maybe team to be general) buys)
#     """
#     pass

@dataclass
class DeathEvent(Event):
    """
    When a player dies
    Will be useful for tracking environmental deaths
    """
    player: PositionedPlayer

    def __str__(self) -> str:
        return f"{self.player} died"

@dataclass
class SmokeSpawnEvent(Event):
    """
    When a smoke spawns
    """
    grenade_entity_id: int
    position: Position

    def __str__(self) -> str:
        return f"Smoke {self.grenade_entity_id} spawned at {self.position}"

@dataclass
class SmokeDespawnEvent(Event):
    """
    When a smoke despawns
    """
    grenade_entity_id: int
    position: Position

    def __str__(self) -> str:
        return f"Smoke {self.grenade_entity_id} despawned at {self.position}"

@dataclass
class FireSpawnEvent(Event):
    """
    When fire spawns
    """
    unique_id: int
    position: Position

    def __str__(self) -> str:
        return f"Fire {self.unique_id} spawned at {self.position}"

@dataclass
class FireDespawnEvent(Event):
    """
    When fire despawns
    """
    unique_id: int
    position: Position

    def __str__(self) -> str:
        return f"Fire {self.unique_id} despawned at {self.position}"

@dataclass
class BombPickupEvent(Event):
    """
    When the bomb enters a player's inventory
    """
    player: PositionedPlayer

    def __str__(self) -> str:
        return f"{self.player} picked up the bomb"

@dataclass
class BombDropEvent(Event):
    """
    When the bomb leaves a player's inventory
    # Note: one of these will occur on bomb plant
    """
    player: PositionedPlayer

    def __str__(self) -> str:
        return f"{self.player} dropped the bomb (or planted it)"

# TODO: Maybe add a 'reload' event? Or a 'switch weapon' event?

@dataclass
class RoundStartEvent():
    """
    When the round starts
    Does not inherit from Event because it only has tick
    """
    tick: int
    ct_score: int
    t_score: int
    ct_equipment_value: int
    t_equipment_value: int

    def __str__(self) -> str:
        return f"New round started - CT/T equipment values: {self.ct_equipment_value}/{self.t_equipment_value}"

@dataclass
class FreezeTimeEndEvent():
    """
    When the freeze time ends
    """
    tick: int
    ct_equipment_value: int
    t_equipment_value: int
    ct_money_spent: int
    t_money_spent: int
    ct_buy_type: str
    t_buy_type: str

    def __str__(self) -> str:
        return f"Freeze time ended - CT/T equipment values: {self.ct_equipment_value}/{self.t_equipment_value}, CT/T money spent: {self.ct_money_spent}({self.ct_buy_type})/{self.t_money_spent}({self.t_buy_type})"

@dataclass
class RoundEndEvent():
    """
    When the round ends
    Does not inherit from Event because it only has tick
    """
    tick: int
    official_tick: int
    reason: str
    winning_side: Side
    winning_team: str
    losing_team: str
    end_ct_score: int
    end_t_score: int

    def __str__(self) -> str:
        return f"Round ended - {self.winning_team} ({self.winning_side}) wins ({self.reason}), CT {self.end_ct_score} - T {self.end_t_score}"

@dataclass
class Timeline:
    events: list[Event]
    # TODO: Add more stuff here as necessary

    def __str__(self) -> str:
        return "\n".join([str(event) for event in self.events])            

@dataclass
class Game:
    """
    The structure/purpose of this class is super undecided so figure it out later TODO
    """
    players: list[Player]
    timeline: Timeline

def create_timeline(demo: models.Demo) -> Timeline:
    """
    Go through the demo file and create appropriate event objects and add them to a Timeline
    """
    timeline: Timeline = Timeline(events=[])

    connection_events: list[PlayerConnectionEvent] = []
    for connection in demo.player_connections:
        connection_events.append(PlayerConnectionEvent(
            tick=connection.tick,
            steam_id=connection.steam_id,
            action=connection.action,
        ))
    timeline.events.extend(connection_events)

    for round in demo.game_rounds:
        """
        Objects:
            dict_keys(['round_number', 'is_warmup', 'start_tick', 'freeze_time_end_tick', 'end_tick', 'end_official_tick', 'bomb_plant_tick', 
            't_score', 'ct_score', 'end_t_score', 'end_ct_score', 'ct_team', 't_team', 'winning_side', 'winning_team', 'losing_team', 
            'round_end_reason', 'ct_freeze_time_end_eq_val', 'ct_round_start_eq_val', 'ct_round_spend_money', 'ct_buy_type', 
            't_freeze_time_end_eq_val', 't_round_start_eq_val', 't_round_spend_money', 't_buy_type', 'ct_side', 't_side', 'kills', 'damages', 
            'grenades', 'bomb_events', 'weapon_fires', 'flashes', 'frames'])

        Objects of note:
            round start event
            freeze time end event
            round end event
            1 event per:
                kills
                damages
                grenades
                bomb_events
                weapon_fires
                flashes
            1 event per frame in frames
            1 event (place at start of round) for what each team bought
        """

        round_start_event = RoundStartEvent(
            tick=round.start_tick,
            ct_score=round.ct_score,
            t_score=round.t_score,
            ct_equipment_value=round.ct_round_start_eq_val,
            t_equipment_value=round.t_round_start_eq_val,
        )
        timeline.events.append(round_start_event)

        freeze_time_end_event = FreezeTimeEndEvent(
            tick=round.freeze_time_end_tick,
            ct_equipment_value=round.ct_freeze_time_end_eq_val,
            t_equipment_value=round.t_freeze_time_end_eq_val,
            ct_money_spent=round.ct_round_spend_money,
            t_money_spent=round.t_round_spend_money,
            ct_buy_type=round.ct_buy_type,
            t_buy_type=round.t_buy_type
        )
        timeline.events.append(freeze_time_end_event)

        round_end_event = RoundEndEvent(
            tick=round.end_tick,
            official_tick=round.end_official_tick,
            reason=round.round_end_reason,
            winning_side=Side.from_acronym(round.winning_side),
            winning_team=round.winning_team,
            losing_team=round.losing_team,
            end_ct_score=round.end_ct_score,
            end_t_score=round.end_t_score
        )
        timeline.events.append(round_end_event)

        kill_events: list[KillEvent] = []
        for kill in round.kills:
            attacker: PositionedPlayerWithView = PositionedPlayerWithView(
                steam_id=kill.attacker_steam_id,
                team=kill.attacker_team,
                side=Side.from_acronym(kill.attacker_side),
                name=kill.attacker_name,
                position=Position(
                    x=kill.attacker_x,
                    y=kill.attacker_y,
                    z=kill.attacker_z,
                ),
                view=View(
                    x=kill.attacker_view_x,
                    y=kill.attacker_view_y,
                )
            )
            victim: PositionedPlayerWithView = PositionedPlayerWithView(
                steam_id=kill.victim_steam_id,
                team=kill.victim_team,
                side=Side.from_acronym(kill.victim_side),
                name=kill.victim_name,
                position=Position(
                    x=kill.victim_x,
                    y=kill.victim_y,
                    z=kill.victim_z,
                ),
                view=View(
                    x=kill.victim_view_x,
                    y=kill.victim_view_y,
                )
            )
            assister: Player | None = None
            if kill.assister_steam_id is not None:
                assister = Player(
                    steam_id=kill.assister_steam_id,
                    team=kill.assister_team,
                    side=Side.from_acronym(kill.assister_side),
                    name=kill.assister_name,
                )
            flash_thrower: Player | None = None
            if kill.flash_thrower_steam_id is not None:
                flash_thrower = Player(
                    steam_id=kill.flash_thrower_steam_id,
                    team=kill.flash_thrower_team,
                    side=Side.from_acronym(kill.flash_thrower_side),
                    name=kill.flash_thrower_name,
                )
            player_traded: Player | None = None
            if kill.player_traded_steam_id is not None:
                player_traded = Player(
                    steam_id=kill.player_traded_steam_id,
                    team=kill.player_traded_team,
                    # This Side inference might not always be correct
                    side=Side.invert(Side.from_acronym(kill.attacker_side)),
                    name=kill.player_traded_name,
                )
            weapon: Weapon = Weapon(
                name=kill.weapon,
                weapon_class=kill.weapon_class,
                ammo_in_magazine=None,  # This info is not available
                ammo_in_reserve=None,   # This info is not available
            )

            kill_events.append(KillEvent(
                tick=kill.tick,
                seconds=kill.seconds,
                clock_time=kill.clock_time,
                attacker=attacker,
                victim=victim,
                assister=assister,
                is_suicide=kill.is_suicide,
                is_teamkill=kill.is_teamkill,
                is_wallbang=kill.is_wallbang,
                penetrated_objects=kill.penetrated_objects,
                is_first_kill=kill.is_first_kill,
                is_headshot=kill.is_headshot,
                is_victim_blinded=kill.is_victim_blinded,
                is_attacker_blinded=kill.is_attacker_blinded,
                flash_thrower=flash_thrower,
                is_no_scope=kill.is_no_scope,
                is_through_smoke=kill.is_through_smoke,
                distance=kill.distance,
                # is_trade: bool
                player_traded=player_traded,
                weapon=weapon,
            ))
        timeline.events.extend(kill_events)

        damage_events: list[DamageEvent] = []
        for damage in round.damages:
            attacker = PositionedPlayerWithView(
                steam_id=damage.attacker_steam_id,
                team=damage.attacker_team,
                side=Side.from_acronym(damage.attacker_side),
                name=damage.attacker_name,
                position=Position(
                    x=damage.attacker_x,
                    y=damage.attacker_y,
                    z=damage.attacker_z,
                ),
                view=View(
                    x=damage.attacker_view_x,
                    y=damage.attacker_view_y,
                )
            )

            victim = PositionedPlayerWithView(
                steam_id=damage.victim_steam_id,
                team=damage.victim_team,
                side=Side.from_acronym(damage.victim_side),
                name=damage.victim_name,
                position=Position(
                    x=damage.victim_x,
                    y=damage.victim_y,
                    z=damage.victim_z,
                ),
                view=View(
                    x=damage.victim_view_x,
                    y=damage.victim_view_y,
                )
            )

            weapon = Weapon(
                name=damage.weapon,
                weapon_class=damage.weapon_class,
                ammo_in_magazine=None,  # This info is not available
                ammo_in_reserve=None,   # This info is not available
            )

            damage_events.append(DamageEvent(
                tick=damage.tick,
                seconds=damage.seconds,
                clock_time=damage.clock_time,
                attacker=attacker,
                is_attacker_strafe=damage.is_attacker_strafe,
                victim=victim,
                weapon=weapon,
                hp_damage=damage.hp_damage,
                hp_damage_taken=damage.hp_damage_taken,
                armor_damage=damage.armor_damage,
                armor_damage_taken=damage.armor_damage_taken,
                hit_group=damage.hit_group,
                is_friendly_fire=damage.is_friendly_fire,
                distance=damage.distance,
                zoom_level=damage.zoom_level,
            ))
        timeline.events.extend(kill_events)

        grenade_throw_events: list[GrenadeThrowEvent] = []
        grenade_trigger_events: list[GrenadeTriggerEvent] = []
        for grenade in round.grenades:
            thrower = PositionedPlayer(
                steam_id=grenade.thrower_steam_id,
                team=grenade.thrower_team,
                side=Side.from_acronym(grenade.thrower_side),
                name=grenade.thrower_name,
                position=Position(
                    x=grenade.thrower_x,
                    y=grenade.thrower_y,
                    z=grenade.thrower_z,
                )
            )

            grenade_throw_events.append(GrenadeThrowEvent(
                tick=grenade.throw_tick,
                seconds=grenade.throw_seconds,
                clock_time=grenade.throw_clock_time,
                entity_id=grenade.entity_id,
                grenade_type=grenade.grenade_type,
                thrower=thrower,
            ))

            grenade_trigger_events.append(GrenadeTriggerEvent(
                tick=grenade.destroy_tick,
                seconds=grenade.destroy_seconds,
                clock_time=grenade.destroy_clock_time,
                entity_id=grenade.entity_id,
                grenade_type=grenade.grenade_type,
                position=Position(
                    x=grenade.grenade_x,
                    y=grenade.grenade_y,
                    z=grenade.grenade_z,
                )
            ))
        timeline.events.extend(grenade_throw_events)
        timeline.events.extend(grenade_trigger_events)

        bomb_events: list[BombEvent] = []
        for bomb in round.bomb_events:
            player_frame = PositionedPlayer(
                steam_id=bomb.player_steam_id,
                team=bomb.player_team,
                side=Side.from_bomb_action(bomb.bomb_action),
                name=bomb.player_name,
                position=Position(
                    x=bomb.player_x,
                    y=bomb.player_y,
                    z=bomb.player_z,
                )
            )

            bomb_events.append(BombEvent(
                tick=bomb.tick,
                seconds=bomb.seconds,
                clock_time=bomb.clock_time,
                player=player_frame,
                bomb_action=bomb.bomb_action,
                bomb_site=bomb.bomb_site,
            ))
            pass
        timeline.events.extend(bomb_events)
        
        weapon_fire_events: list[WeaponFireEvent] = []
        for weapon_fire in round.weapon_fires:
            weapon_fire_events.append(WeaponFireEvent(
                tick=weapon_fire.tick,
                seconds=weapon_fire.seconds,
                clock_time=weapon_fire.clock_time,
                player=PositionedPlayerWithView(
                    steam_id=weapon_fire.player_steam_id,
                    team=weapon_fire.player_team,
                    side=Side.from_acronym(weapon_fire.player_side),
                    name=weapon_fire.player_name,
                    position=Position(
                        x=weapon_fire.player_x,
                        y=weapon_fire.player_y,
                        z=weapon_fire.player_z,
                    ),
                    view=View(
                        x=weapon_fire.player_view_x,
                        y=weapon_fire.player_view_y,
                    )
                ),
                is_player_strafe=weapon_fire.is_player_strafe,
                weapon=Weapon(
                    name=weapon_fire.weapon,
                    weapon_class=weapon_fire.weapon_class,
                    ammo_in_magazine=weapon_fire.ammo_in_magazine,
                    ammo_in_reserve=weapon_fire.ammo_in_reserve,
                ),
                zoom_level=weapon_fire.zoom_level,
            ))
        timeline.events.extend(weapon_fire_events)

        flash_events: list[FlashEvent] = []
        for flash in round.flashes:
            flash_events.append(FlashEvent(
                tick=flash.tick,
                seconds=flash.seconds,
                clock_time=flash.clock_time,
                attacker=PositionedPlayerWithView(
                    steam_id=flash.attacker_steam_id,
                    team=flash.attacker_team,
                    side=Side.from_acronym(flash.attacker_side),
                    name=flash.attacker_name,
                    position=Position(
                        x=flash.attacker_x,
                        y=flash.attacker_y,
                        z=flash.attacker_z,
                    ),
                    view=View(
                        x=flash.attacker_view_x,
                        y=flash.attacker_view_y,
                    ),
                ),
                player=PositionedPlayerWithView(
                    steam_id=flash.player_steam_id,
                    team=flash.player_team,
                    side=Side.from_acronym(flash.player_side),
                    name=flash.player_name,
                    position=Position(
                        x=flash.player_x,
                        y=flash.player_y,
                        z=flash.player_z,
                    ),
                    view=View(
                        x=flash.player_view_x,
                        y=flash.player_view_y,
                    ),
                ),
                flash_duration=flash.flash_duration,
            ))
        timeline.events.extend(flash_events)

        # TODO: Each frame tracks game state
        # Use this to, by progressing through each frame,
        # Detect when:
        # 1. a player significantly changes movement
        # ->    What this means is TBD
        # ->    a. Stops moving
        # ->    b. Starts moving
        # ->    c. Direction changes by more than a certain amount (15 degrees?)
        # ->    d. Speed drops by like 70%
        # 2. a player starts reloading
        # 3. a player scopes
        # 4. a player switches weapons
        # 5. a player's inventory changes
        # 6. a player buys something from the store
        # 7. a player dies (this might be redundant)
        # 8. smoke spawns
        # 9. smoke despawns
        # 10.fire spawns
        # 11.fire despawns
        # 12.when a player picks up the bomb
        
        # Defining a default initial frame
        # to make the for loop easier to write
        # TODO Maybe just make this the first frame
        # previous_frame = models.Frame(
        #     is_kill_frame=False,
        #     tick=None,
        #     seconds=None,
        #     clock_time=None,
        #     t=models.TeamFrameState(
        #         side=Side.T,
        #         team_name=None,
        #         team_eq_val=None,
        #         alive_players=None,
        #         total_utility=None,
        #         players=[],
        #     ),
        #     ct=models.TeamFrameState(
        #         side=Side.CT,
        #         team_name=None,
        #         team_eq_val=None,
        #         alive_players=None,
        #         total_utility=None,
        #         players=[],
        #     ),
        #     bomb_planted=False,
        #     bomb_site=None,
        #     bomb=models.Bomb(
        #         x=None,
        #         y=None,
        #         z=None,
        #     ),
        #     projectiles=[],
        #     smokes=[],
        #     fires=[],
        # )
        previous_frame = round.frames[0]
        for frame in round.frames[1:]:
            # Perform checks!

            previous_team_frame: models.TeamFrameState
            team_frame: models.TeamFrameState
            previous_player_frame: models.PlayerFrameState = None
            player_frame: models.PlayerFrameState = None
            for (previous_team_frame, team_frame) in [(previous_frame.ct, frame.ct), (previous_frame.t, frame.t)]:
                for (previous_player_frame, player_frame) in zip(previous_team_frame.players, team_frame.players): # Maybe change this to team.alive_players if I want to
                    
                    # Stop moving check
                    if player_frame.is_moving() == False and previous_player_frame.is_moving() == True:
                        timeline.events.append(StoppingMovingEvent(
                            tick=frame.tick,
                            seconds=frame.seconds,
                            clock_time=frame.clock_time,
                            player=PositionedPlayerWithView(
                                steam_id=player_frame.steam_id,
                                team=player_frame.team,
                                side=Side.from_acronym(player_frame.side),
                                name=player_frame.name,
                                position=Position(
                                    x=player_frame.x,
                                    y=player_frame.y,
                                    z=player_frame.z,
                                ),
                                view=View(
                                    x=player_frame.view_x,
                                    y=player_frame.view_y,
                                ),
                            ),
                        ))
                        
                    # Start moving check
                    if player_frame.is_moving() == True and previous_player_frame.is_moving() == False:
                        timeline.events.append(StoppingMovingEvent(
                            tick=frame.tick,
                            seconds=frame.seconds,
                            clock_time=frame.clock_time,
                            player=PositionedPlayerWithView(
                                steam_id=player_frame.steam_id,
                                team=player_frame.team,
                                side=Side.from_acronym(player_frame.side),
                                name=player_frame.name,
                                position=Position(
                                    x=player_frame.x,
                                    y=player_frame.y,
                                    z=player_frame.z,
                                ),
                                view=View(
                                    x=player_frame.view_x,
                                    y=player_frame.view_y,
                                ),
                            ),
                        ))

                    # Direction change check
                    v1 = (player_frame.velocity_x, player_frame.velocity_y, player_frame.velocity_z)
                    v2 = (previous_player_frame.velocity_x, previous_player_frame.velocity_y, previous_player_frame.velocity_z)
                    degrees_apart = 180*np.arccos(np.dot(v1,v2)/(np.linalg.norm(v1)*np.linalg.norm(v2)))/np.pi
                    SIGNIFICANT_DEGREE_CHANGE: float = 15.0
                    if degrees_apart > SIGNIFICANT_DEGREE_CHANGE:
                        timeline.events.append(DirectionChangeEvent(
                            tick=frame.tick,
                            seconds=frame.seconds,
                            clock_time=frame.clock_time,
                            player=PositionedPlayerWithView(
                                steam_id=player_frame.steam_id,
                                team=player_frame.team,
                                side=Side.from_acronym(player_frame.side),
                                name=player_frame.name,
                                position=Position(
                                    x=player_frame.x,
                                    y=player_frame.y,
                                    z=player_frame.z,
                                ),
                                view=View(
                                    x=player_frame.view_x,
                                    y=player_frame.view_y,
                                ),
                            ),
                            old_velocity=v2,
                            new_velocity=v1,
                        ))

                    # Speed drop check
                    player_speed = np.linalg.norm([player_frame.velocity_x, player_frame.velocity_y, player_frame.velocity_z])
                    last_frame_player_speed = np.linalg.norm([previous_player_frame.velocity_x, previous_player_frame.velocity_y, previous_player_frame.velocity_z])
                    SIGNIFICANT_SPEED_CUT: float = 0.7
                    if player_speed < last_frame_player_speed*SIGNIFICANT_SPEED_CUT:
                        timeline.events.append(SlowedSpeedEvent(
                            tick=frame.tick,
                            seconds=frame.seconds,
                            clock_time=frame.clock_time,
                            player=PositionedPlayerWithView(
                                steam_id=player_frame.steam_id,
                                team=player_frame.team,
                                side=Side.from_acronym(player_frame.side),
                                name=player_frame.name,
                                position=Position(
                                    x=player_frame.x,
                                    y=player_frame.y,
                                    z=player_frame.z,
                                ),
                                view=View(
                                    x=player_frame.view_x,
                                    y=player_frame.view_y,
                                ),
                            ),
                            old_speed=last_frame_player_speed,
                            new_speed=player_speed,
                        ))

                    # Reload start check
                    if player_frame.is_reloading == True and previous_player_frame.is_reloading == False:
                        timeline.events.append(ReloadStartEvent(
                            tick=frame.tick,
                            seconds=frame.seconds,
                            clock_time=frame.clock_time,
                            player=PositionedPlayerWithView(
                                steam_id=player_frame.steam_id,
                                team=player_frame.team,
                                side=Side.from_acronym(player_frame.side),
                                name=player_frame.name,
                                position=Position(
                                    x=player_frame.x,
                                    y=player_frame.y,
                                    z=player_frame.z,
                                ),
                                view=View(
                                    x=player_frame.view_x,
                                    y=player_frame.view_y,
                                ),
                            ),
                            weapon=player_frame.inventory[0],
                        ))

                    # Reload finish check
                    if (
                        player_frame.is_reloading == False and previous_player_frame.is_reloading == True and
                        len(player_frame.inventory) > 0 and len(previous_player_frame.inventory) > 0 and
                        player_frame.inventory[0] == previous_player_frame.inventory[0] and
                        player_frame.inventory[0].ammo_in_magazine > previous_player_frame.inventory[0].ammo_in_magazine
                    ):
                        timeline.events.append(ReloadFinishEvent(
                            tick=frame.tick,
                            seconds=frame.seconds,
                            clock_time=frame.clock_time,
                            player=PositionedPlayerWithView(
                                steam_id=player_frame.steam_id,
                                team=player_frame.team,
                                side=Side.from_acronym(player_frame.side),
                                name=player_frame.name,
                                position=Position(
                                    x=player_frame.x,
                                    y=player_frame.y,
                                    z=player_frame.z,
                                ),
                                view=View(
                                    x=player_frame.view_x,
                                    y=player_frame.view_y,
                                ),
                            ),
                            weapon=player_frame.inventory[0],
                        ))

                    # Reload cancel check
                    if (
                        player_frame.is_reloading == False and previous_player_frame.is_reloading == True and
                        len(player_frame.inventory) > 0 and len(previous_player_frame.inventory) > 0 and
                        (player_frame.inventory[0] != previous_player_frame.inventory[0] or
                        player_frame.inventory[0].ammo_in_magazine <= previous_player_frame.inventory[0].ammo_in_magazine)
                    ):
                        timeline.events.append(ReloadCancelEvent(
                            tick=frame.tick,
                            seconds=frame.seconds,
                            clock_time=frame.clock_time,
                            player=PositionedPlayerWithView(
                                steam_id=player_frame.steam_id,
                                team=player_frame.team,
                                side=Side.from_acronym(player_frame.side),
                                name=player_frame.name,
                                position=Position(
                                    x=player_frame.x,
                                    y=player_frame.y,
                                    z=player_frame.z,
                                ),
                                view=View(
                                    x=player_frame.view_x,
                                    y=player_frame.view_y,
                                ),
                            ),
                            # weapon=player_frame.inventory[0],
                            weapon=previous_player_frame.inventory[0],
                        ))

                    # Scope check
                    if player_frame.is_scoped == True and previous_player_frame.is_scoped == False:
                        timeline.events.append(ScopeEvent(
                            tick=frame.tick,
                            seconds=frame.seconds,
                            clock_time=frame.clock_time,
                            player=PositionedPlayerWithView(
                                steam_id=player_frame.steam_id,
                                team=player_frame.team,
                                side=Side.from_acronym(player_frame.side),
                                name=player_frame.name,
                                position=Position(
                                    x=player_frame.x,
                                    y=player_frame.y,
                                    z=player_frame.z,
                                ),
                                view=View(
                                    x=player_frame.view_x,
                                    y=player_frame.view_y,
                                ),
                            ),
                            weapon=player_frame.inventory[0],
                        ))

                    # Unscope check
                    if player_frame.is_scoped == False and previous_player_frame.is_scoped == True:
                        timeline.events.append(UnscopeEvent(
                            tick=frame.tick,
                            seconds=frame.seconds,
                            clock_time=frame.clock_time,
                            player=PositionedPlayerWithView(
                                steam_id=player_frame.steam_id,
                                team=player_frame.team,
                                side=Side.from_acronym(player_frame.side),
                                name=player_frame.name,
                                position=Position(
                                    x=player_frame.x,
                                    y=player_frame.y,
                                    z=player_frame.z,
                                ),
                                view=View(
                                    x=player_frame.view_x,
                                    y=player_frame.view_y,
                                ),
                            ),
                            weapon=player_frame.inventory[0] if len(player_frame.inventory) > 0 else None,
                        ))

                    # Switch weapon check
                    if (
                        len(player_frame.inventory) > 0 and len(previous_player_frame.inventory) > 0 and
                        player_frame.inventory[0] != previous_player_frame.inventory[0]
                    ):
                        timeline.events.append(WeaponSwitchEvent(
                            tick=frame.tick,
                            seconds=frame.seconds,
                            clock_time=frame.clock_time,
                            player=PositionedPlayerWithView(
                                steam_id=player_frame.steam_id,
                                team=player_frame.team,
                                side=Side.from_acronym(player_frame.side),
                                name=player_frame.name,
                                position=Position(
                                    x=player_frame.x,
                                    y=player_frame.y,
                                    z=player_frame.z,
                                ),
                                view=View(
                                    x=player_frame.view_x,
                                    y=player_frame.view_y,
                                ),
                            ),
                            previous_weapon=previous_player_frame.inventory[0],
                            new_weapon=player_frame.inventory[0],
                        ))

                    # Inventory change check
                    combined_inventory: list[Weapon] = player_frame.inventory + previous_player_frame.inventory
                    inventory_difference = [w for w in combined_inventory if w not in player_frame.inventory or w not in previous_player_frame.inventory]
                    if len(inventory_difference) > 0:
                        timeline.events.append(InventoryChangeEvent(
                            tick=frame.tick,
                            seconds=frame.seconds,
                            clock_time=frame.clock_time,
                            player=PositionedPlayerWithView(
                                steam_id=player_frame.steam_id,
                                team=player_frame.team,
                                side=Side.from_acronym(player_frame.side),
                                name=player_frame.name,
                                position=Position(
                                    x=player_frame.x,
                                    y=player_frame.y,
                                    z=player_frame.z,
                                ),
                                view=View(
                                    x=player_frame.view_x,
                                    y=player_frame.view_y,
                                ),
                            ),
                            old_inventory=previous_player_frame.inventory,
                            updated_inventory=player_frame.inventory,
                        ))

                    # Buy check
                    # TODO: Do this if we are implementing BuyCheckEvent(s)

                    # Death check
                    if player_frame.is_alive == False and previous_player_frame.is_alive == True:
                        timeline.events.append(DeathEvent(
                            tick=frame.tick,
                            seconds=frame.seconds,
                            clock_time=frame.clock_time,
                            player=PositionedPlayer(
                                steam_id=player_frame.steam_id,
                                team=player_frame.team,
                                side=Side.from_acronym(player_frame.side),
                                name=player_frame.name,
                                position=Position(
                                    x=player_frame.x,
                                    y=player_frame.y,
                                    z=player_frame.z,
                                ),
                            ),
                        ))

                    # Bomb pickup check
                    if player_frame.has_bomb == True and previous_player_frame.has_bomb == False:
                        timeline.events.append(BombPickupEvent(
                            tick=frame.tick,
                            seconds=frame.seconds,
                            clock_time=frame.clock_time,
                            player=PositionedPlayer(
                                steam_id=player_frame.steam_id,
                                team=player_frame.team,
                                side=Side.from_acronym(player_frame.side),
                                name=player_frame.name,
                                position=Position(
                                    x=player_frame.x,
                                    y=player_frame.y,
                                    z=player_frame.z,
                                ),
                            ),
                        ))

                    # Bomb drop check
                    if player_frame.has_bomb == False and previous_player_frame.has_bomb == True:
                        timeline.events.append(BombDropEvent(
                            tick=frame.tick,
                            seconds=frame.seconds,
                            clock_time=frame.clock_time,
                            player=PositionedPlayer(
                                steam_id=player_frame.steam_id,
                                team=player_frame.team,
                                side=Side.from_acronym(player_frame.side),
                                name=player_frame.name,
                                position=Position(
                                    x=player_frame.x,
                                    y=player_frame.y,
                                    z=player_frame.z,
                                ),
                            ),
                        ))

            # Non-team specific checks:

            # Smoke spawn/despawn check
            current_smokes: list[models.Smoke] = frame.smokes
            previous_smokes: list[models.Smoke] = previous_frame.smokes
            spawned_smokes: list[models.Smoke] = [s for s in current_smokes if s not in previous_smokes]
            despawned_smokes: list[models.Smoke] = [s for s in previous_smokes if s not in current_smokes]
            for smoke in spawned_smokes:
                timeline.events.append(SmokeSpawnEvent(
                    tick=frame.tick,
                    seconds=frame.seconds,
                    clock_time=frame.clock_time,
                    grenade_entity_id=smoke.grenade_entity_id,
                    position=Position(
                        x=smoke.x,
                        y=smoke.y,
                        z=smoke.z,
                    )
                ))
            for smoke in despawned_smokes:
                timeline.events.append(SmokeDespawnEvent(
                    tick=frame.tick,
                    seconds=frame.seconds,
                    clock_time=frame.clock_time,
                    grenade_entity_id=smoke.grenade_entity_id,
                    position=Position(
                        x=smoke.x,
                        y=smoke.y,
                        z=smoke.z,
                    )
                ))

            # Fire spawn/despawn check
            current_fires: list[models.Fire] = frame.fires
            previous_fires: list[models.Fire] = previous_frame.fires
            spawned_fires: list[models.Fire] = [f for f in current_fires if f not in previous_fires]
            despawned_fires: list[models.Fire] = [f for f in previous_fires if f not in current_fires]
            for fire in spawned_fires:
                timeline.events.append(FireSpawnEvent(
                    tick=frame.tick,
                    seconds=frame.seconds,
                    clock_time=frame.clock_time,
                    unique_id=fire.unique_id,
                    position=Position(
                        x=fire.x,
                        y=fire.y,
                        z=fire.z,
                    )
                ))
            for fire in despawned_fires:
                timeline.events.append(FireDespawnEvent(
                    tick=frame.tick,
                    seconds=frame.seconds,
                    clock_time=frame.clock_time,
                    unique_id=fire.unique_id,
                    position=Position(
                        x=fire.x,
                        y=fire.y,
                        z=fire.z,
                    )
                ))

            previous_frame = frame

    # Sort events into chronological order
    sorted_timeline = Timeline(events=sorted(timeline.events, key=lambda event: event.tick))
    return sorted_timeline

# TODO: Add __str__ methods to every data class
