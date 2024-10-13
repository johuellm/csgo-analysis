from dataclasses import dataclass

# NOTE: Most of this file has become obsolete because awpy has added type information to the library.
# I am not deleting it though because these classes are still used in certain execution paths of the program.

@dataclass
class ParserParameters:
    parse_rate: int
    do_parse_frames: bool
    do_parse_kill_frames: bool
    trade_time: int
    round_buy_style: str
    are_damages_rolled_up: bool

@dataclass
class ServerVars:
    cash_bomb_defused: int
    cash_bomb_planted: int
    cash_team_t_win_bomb: int
    cash_win_defuse: int
    cash_win_time_run_out: int
    cash_win_elimination: int
    cash_player_killed_default: int
    cash_team_loser_bonus: int
    cash_team_loser_bonus_consecutive: int
    round_time: int
    round_time_defuse: int
    round_restart_delay: int
    freeze_time: int
    buy_time: int
    bomb_timer: int
    max_rounds: int
    timeouts_allowed: int
    coaching_allowed: int

@dataclass
class MatchPhases:
    announcement_last_round_half: list[int]
    announcement_final_round: list[int]
    announcement_match_started: list[int]
    round_started: list[int]
    round_ended: list[int]
    round_freeze_time_ended: list[int]
    round_ended_official: list[int]
    game_half_ended: list[int]
    match_start: list[int]
    match_started_changed: list[int]
    warmup_changed: list[int]
    team_switch: list[int]

@dataclass
class PlayerConnection:
    tick: int
    action: str # From what I can tell options are "connect" and "disconnect"
    steam_id: int

@dataclass
class Player:
    player_name: str
    steam_id: int

@dataclass
class Team:
    team_name: str
    players: list[Player]

@dataclass
class Kill:
    tick: int
    seconds: float
    clock_time: str
    attacker_steam_id: int
    attacker_name: str
    attacker_team: str
    attacker_side: str
    attacker_x: float
    attacker_y: float
    attacker_z: float
    attacker_view_x: float
    attacker_view_y: float
    victim_steam_id: int
    victim_name: str
    victim_team: str
    victim_side: str
    victim_x: float
    victim_y: float
    victim_z: float
    victim_view_x: float
    victim_view_y: float
    assister_steam_id: int | None
    assister_name: str | None
    assister_team: str | None
    assister_side: str | None
    is_suicide: bool
    is_teamkill: bool
    is_wallbang: bool
    penetrated_objects: int
    is_first_kill: bool
    is_headshot: bool
    is_victim_blinded: bool
    is_attacker_blinded: bool
    flash_thrower_steam_id: int | None
    flash_thrower_name: str | None
    flash_thrower_team: str | None
    flash_thrower_side: str | None
    is_no_scope: bool
    is_through_smoke: bool
    distance: float
    is_trade: bool
    player_traded_name: str | None
    player_traded_team: str | None
    player_traded_steam_id: int | None
    weapon: str
    weapon_class: str

@dataclass
class Damage:
    tick: int
    seconds: float
    clock_time: str
    attacker_steam_id: int
    attacker_name: str
    attacker_team: str
    attacker_side: str
    attacker_x: float
    attacker_y: float
    attacker_z: float
    attacker_view_x: float
    attacker_view_y: float
    is_attacker_strafe: bool # I don't entirely know what this refers to so maybe it should be did_attacker_strafe ?
    victim_steam_id: int
    victim_name: str
    victim_team: str
    victim_side: str
    victim_x: float
    victim_y: float
    victim_z: float
    victim_view_x: float
    victim_view_y: float
    weapon: str
    weapon_class: str
    hp_damage: int
    hp_damage_taken: int
    armor_damage: int
    armor_damage_taken: int
    hit_group: str
    is_friendly_fire: bool
    distance: float
    zoom_level: int

@dataclass
class Grenade:
    throw_tick: int
    destroy_tick: int
    throw_seconds: float
    throw_clock_time: str
    destroy_seconds: float
    destroy_clock_time: str
    thrower_steam_id: int
    thrower_name: str
    thrower_team: str
    thrower_side: str
    thrower_x: float
    thrower_y: float
    thrower_z: float
    grenade_type: str # i.e. "Flashbang", "Molotov", "HE Grenade", "Decoy Grenade", "Incendiary Grenade", etc.
    grenade_x: float
    grenade_y: float
    grenade_z: float
    entity_id: int

@dataclass
class BombEvent:
    tick: int
    seconds: float
    clock_time: str
    player_steam_id: int
    player_name: str
    player_team: str
    player_x: float
    player_y: float
    player_z: float
    bomb_action: str # i.e. "plant_begin", "plant_abort", TODO ADD MORE EXAMPLES?
    bomb_site: str # i.e. "A"

@dataclass
class WeaponFire:
    tick: int
    seconds: float
    clock_time: str
    player_steam_id: int
    player_name: str
    player_team: str
    player_side: str
    player_x: float
    player_y: float
    player_z: float
    player_view_x: float
    player_view_y: float
    is_player_strafe: bool
    weapon: str
    weapon_class: str
    ammo_in_magazine: int
    ammo_in_reserve: int
    zoom_level: int

@dataclass
class Flash:
    tick: int
    seconds: float
    clock_time: str
    attacker_steam_id: int
    attacker_name: str
    attacker_team: str
    attacker_side: str
    attacker_x: float
    attacker_y: float
    attacker_z: float
    attacker_view_x: float
    attacker_view_y: float
    player_steam_id: int
    player_name: str
    player_team: str
    player_side: str
    player_x: float
    player_y: float
    player_z: float
    player_view_x: float
    player_view_y: float
    flash_duration: float

@dataclass
class Weapon:
    weapon_name: str
    weapon_class: str
    ammo_in_magazine: int
    ammo_in_reserve: int

@dataclass
class PlayerFrameState:
    """
    Data about a player, a snapshot of their metrics during one frame.
    """
    steam_id: int
    name: str
    team: str
    side: str
    x: float
    y: float
    z: float
    velocity_x: float
    velocity_y: float
    velocity_z: float
    view_x: float # degrees left/right (looking straight east is 0, north is 90, west is 180, south is 270) (YAW) 
    view_y: float # degrees above/below horizon (straight down is 90, straight up is 270) (PITCH)
    hp: int
    armor: int
    active_weapon: str
    total_utility: int
    is_alive: bool
    is_blinded: bool
    is_airborne: bool
    is_ducking: bool
    is_ducking_in_progress: bool
    is_unducking_in_progress: bool
    is_defusing: bool
    is_planting: bool
    is_reloading: bool
    is_in_bomb_zone: bool
    is_in_buy_zone: bool
    is_standing: bool
    is_scoped: bool
    is_walking: bool
    is_unknown: bool # What is this? LOL
    inventory: list[Weapon] | None
    spotters: list # I don't know what this is a list of yet TODO
    equipment_value: int
    equipment_value_freeze_time_end: int
    equipment_value_round_start: int
    cash: int
    cash_spend_this_round: int
    cash_spend_total: int
    has_helmet: bool
    has_defuse_kit: bool
    has_bomb: bool
    ping: int
    zoom_level: int

    def is_moving(self) -> bool:
        """
        Returns whether or not the player is moving.
        """
        return self.velocity_x != 0 or self.velocity_y != 0 or self.velocity_z != 0

@dataclass
class TeamFrameState:
    """
    Data about a team, a snapshot of their metrics during one frame.
    """
    side: str
    team_name: str
    team_eq_val: int # The value of the team's equipment
    alive_players: int
    total_utility: int # The amount of utility items the team owns
    players: list[PlayerFrameState]

@dataclass
class Bomb:
    x: float
    y: float
    z: float

@dataclass
class Projectile:
    projectile_type: str # i.e. "Smoke Grenade"
    x: float
    y: float
    z: float

@dataclass
class Smoke:
    grenade_entity_id: int
    start_tick: int
    x: float
    y: float
    z: float

@dataclass
class Fire:
    unique_id: int
    x: float
    y: float
    z: float

@dataclass
class Frame:
    is_kill_frame: bool
    tick: int
    seconds: float
    clock_time: str
    t: TeamFrameState
    ct: TeamFrameState
    bomb_planted: bool
    bomb_site: str
    bomb: Bomb
    projectiles: list[Projectile]
    smokes: list[Smoke]
    fires: list[Fire]

@dataclass
class Round:
    round_number: int
    is_warmup: bool
    start_tick: int
    freeze_time_end_tick: int
    end_tick: int
    end_official_tick: int # The official end tick of the round is 5 frames after the end tick ((end_official_tick - end_tick)/demo.tick_rate = 5) 
    bomb_plant_tick: int | None
    t_score: int
    ct_score: int
    end_t_score: int
    end_ct_score: int
    ct_team: str # Team name (i.e. 'Cloud9')
    t_team: str # Team name (i.e. 'Outsiders')
    winning_side: str # "CT" or "T"
    winning_team: str # Team name (i.e. 'Cloud9')
    losing_team: str # Team name (i.e. 'Outsiders')
    round_end_reason: str
    ct_freeze_time_end_eq_val: int # The value of the CT team's inventory at the end of freeze time
    ct_round_start_eq_val: int # The value of the CT team's inventory at the start of the round
    ct_round_spend_money: int # The amount of money spent by the CT team in the round
    ct_buy_type: str # A description of the CT team's buy type (i.e. "Full Eco")
    t_freeze_time_end_eq_val: int # The value of the T team's inventory at the end of freeze time
    t_round_start_eq_val: int # The value of the T team's inventory at the start of the round
    t_round_spend_money: int # The amount of money spent by the T team in the round
    t_buy_type: str # A description of the T team's buy type (i.e. "Full Eco")
    ct_side: Team
    t_side: Team
    kills: list[Kill]
    damages: list[Damage]
    grenades: list[Grenade]
    bomb_events: list[BombEvent]
    weapon_fires: list[WeaponFire]
    flashes: list[Flash]
    frames: list[Frame]

@dataclass
class Demo:
    match_id: str
    client_name: str
    map_name: str
    tick_rate: int
    playback_ticks: int
    playback_frames_count: int
    parsed_to_frame_index: int
    parser_parameters: ParserParameters
    server_vars: ServerVars
    match_phases: MatchPhases
    matchmaking_ranks: list # Not sure what the type of is so not specifying
    player_connections: list[PlayerConnection]
    game_rounds: list[Round]

def deserialize_demo_data(demo_file_data: dict) -> Demo:
    player_connections: list[PlayerConnection] = []
    for connection in demo_file_data["playerConnections"]:
        player_connections.append(
            PlayerConnection(
                tick=connection["tick"],
                action=connection["action"],
                steam_id=connection["steamID"],
            )
        )

    game_rounds: list[Round] = []
    for round in demo_file_data["gameRounds"]:
        ct_side: Team
        t_side: Team

        ct_players: list[Player] = []
        for player in round["ctSide"]["players"]:
            ct_players.append(Player(
                player_name=player["playerName"],
                steam_id=player["steamID"],
            ))
        ct_side = Team(
            team_name=round["ctSide"]["teamName"],
            players=ct_players,
        )

        t_players: list[Player] = []
        for player in round["tSide"]["players"]:
            t_players.append(Player(
                player_name=player["playerName"],
                steam_id=player["steamID"],
            ))
        t_side = Team(
            team_name=round["tSide"]["teamName"],
            players=t_players,
        )

        kills: list[Kill] = []
        for kill in round["kills"]:
            kills.append(Kill(
                tick=kill["tick"],
                seconds=kill["seconds"],
                clock_time=kill["clockTime"],
                attacker_steam_id=kill["attackerSteamID"],
                attacker_name=kill["attackerName"],
                attacker_team=kill["attackerTeam"],
                attacker_side=kill["attackerSide"],
                attacker_x=kill["attackerX"],
                attacker_y=kill["attackerY"],
                attacker_z=kill["attackerZ"],
                attacker_view_x=kill["attackerViewX"],
                attacker_view_y=kill["attackerViewY"],
                victim_steam_id=kill["victimSteamID"],
                victim_name=kill["victimName"],
                victim_team=kill["victimTeam"],
                victim_side=kill["victimSide"],
                victim_x=kill["victimX"],
                victim_y=kill["victimY"],
                victim_z=kill["victimZ"],
                victim_view_x=kill["victimViewX"],
                victim_view_y=kill["victimViewY"],
                assister_steam_id=kill["assisterSteamID"],
                assister_name=kill["assisterName"],
                assister_team=kill["assisterTeam"],
                assister_side=kill["assisterSide"],
                is_suicide=kill["isSuicide"],
                is_teamkill=kill["isTeamkill"],
                is_wallbang=kill["isWallbang"],
                penetrated_objects=kill["penetratedObjects"],
                is_first_kill=kill["isFirstKill"],
                is_headshot=kill["isHeadshot"],
                is_victim_blinded=kill["victimBlinded"],
                is_attacker_blinded=kill["attackerBlinded"],
                flash_thrower_steam_id=kill["flashThrowerSteamID"],
                flash_thrower_name=kill["flashThrowerName"],
                flash_thrower_team=kill["flashThrowerTeam"],
                flash_thrower_side=kill["flashThrowerSide"],
                is_no_scope=kill["noScope"],
                is_through_smoke=kill["thruSmoke"],
                distance=kill["distance"],
                is_trade=kill["isTrade"],
                player_traded_name=kill["playerTradedName"],
                player_traded_team=kill["playerTradedTeam"],
                player_traded_steam_id=kill["playerTradedSteamID"],
                weapon=kill["weapon"],
                weapon_class=kill["weaponClass"],
            ))

        damages: list[Damage] = []
        for damage in round["damages"]:
            damages.append(Damage(
                tick=damage["tick"],
                seconds=damage["seconds"],
                clock_time=damage["clockTime"],
                attacker_steam_id=damage["attackerSteamID"],
                attacker_name=damage["attackerName"],
                attacker_team=damage["attackerTeam"],
                attacker_side=damage["attackerSide"],
                attacker_x=damage["attackerX"],
                attacker_y=damage["attackerY"],
                attacker_z=damage["attackerZ"],
                attacker_view_x=damage["attackerViewX"],
                attacker_view_y=damage["attackerViewY"],
                is_attacker_strafe=damage["attackerStrafe"],
                victim_steam_id=damage["victimSteamID"],
                victim_name=damage["victimName"],
                victim_team=damage["victimTeam"],
                victim_side=damage["victimSide"],
                victim_x=damage["victimX"],
                victim_y=damage["victimY"],
                victim_z=damage["victimZ"],
                victim_view_x=damage["victimViewX"],
                victim_view_y=damage["victimViewY"],
                weapon=damage["weapon"],
                weapon_class=damage["weaponClass"],
                hp_damage=damage["hpDamage"],
                hp_damage_taken=damage["hpDamageTaken"],
                armor_damage=damage["armorDamage"],
                armor_damage_taken=damage["armorDamageTaken"],
                hit_group=damage["hitGroup"],
                is_friendly_fire=damage["isFriendlyFire"],
                distance=damage["distance"],
                zoom_level=damage["zoomLevel"],
            ))

        grenades: list[Grenade] = []
        for grenade in round["grenades"]:
            grenades.append(Grenade(
                throw_tick=grenade["throwTick"],
                destroy_tick=grenade["destroyTick"],
                throw_seconds=grenade["throwSeconds"],
                throw_clock_time=grenade["throwClockTime"],
                destroy_seconds=grenade["destroySeconds"],
                destroy_clock_time=grenade["destroyClockTime"],
                thrower_steam_id=grenade["throwerSteamID"],
                thrower_name=grenade["throwerName"],
                thrower_team=grenade["throwerTeam"],
                thrower_side=grenade["throwerSide"],
                thrower_x=grenade["throwerX"],
                thrower_y=grenade["throwerY"],
                thrower_z=grenade["throwerZ"],
                grenade_type=grenade["grenadeType"],
                grenade_x=grenade["grenadeX"],
                grenade_y=grenade["grenadeY"],
                grenade_z=grenade["grenadeZ"],
                entity_id=grenade["entityId"],
            ))

        bomb_events: list[BombEvent] = []
        for bomb_event in round["bombEvents"]:
            bomb_events.append(BombEvent(
                tick=bomb_event["tick"],
                seconds=bomb_event["seconds"],
                clock_time=bomb_event["clockTime"],
                player_steam_id=bomb_event["playerSteamID"],
                player_name=bomb_event["playerName"],
                player_team=bomb_event["playerTeam"],
                player_x=bomb_event["playerX"],
                player_y=bomb_event["playerY"],
                player_z=bomb_event["playerZ"],
                bomb_action=bomb_event["bombAction"],
                bomb_site=bomb_event["bombSite"],
            ))

        weapon_fires: list[WeaponFire] = []
        for weapon_fire in round["weaponFires"]:
            weapon_fires.append(WeaponFire(
                tick=weapon_fire["tick"],
                seconds=weapon_fire["seconds"],
                clock_time=weapon_fire["clockTime"],
                player_steam_id=weapon_fire["playerSteamID"],
                player_name=weapon_fire["playerName"],
                player_team=weapon_fire["playerTeam"],
                player_side=weapon_fire["playerSide"],
                player_x=weapon_fire["playerX"],
                player_y=weapon_fire["playerY"],
                player_z=weapon_fire["playerZ"],
                player_view_x=weapon_fire["playerViewX"],
                player_view_y=weapon_fire["playerViewY"],
                is_player_strafe=weapon_fire["playerStrafe"],
                weapon=weapon_fire["weapon"],
                weapon_class=weapon_fire["weaponClass"],
                ammo_in_magazine=weapon_fire["ammoInMagazine"],
                ammo_in_reserve=weapon_fire["ammoInReserve"],
                zoom_level=weapon_fire["zoomLevel"],
            ))

        flashes: list[Flash] = []
        for flash in round["flashes"]:
            flashes.append(Flash(
                tick=flash["tick"],
                seconds=flash["seconds"],
                clock_time=flash["clockTime"],
                attacker_steam_id=flash["attackerSteamID"],
                attacker_name=flash["attackerName"],
                attacker_team=flash["attackerTeam"],
                attacker_side=flash["attackerSide"],
                attacker_x=flash["attackerX"],
                attacker_y=flash["attackerY"],
                attacker_z=flash["attackerZ"],
                attacker_view_x=flash["attackerViewX"],
                attacker_view_y=flash["attackerViewY"],
                player_steam_id=flash["playerSteamID"],
                player_name=flash["playerName"],
                player_team=flash["playerTeam"],
                player_side=flash["playerSide"],
                player_x=flash["playerX"],
                player_y=flash["playerY"],
                player_z=flash["playerZ"],
                player_view_x=flash["playerViewX"],
                player_view_y=flash["playerViewY"],
                flash_duration=flash["flashDuration"],
            ))

        frames: list[Frame] = []
        for frame in round["frames"]:
            t: TeamFrameState
            
            t_players: list[PlayerFrameState] = []
            for player in frame["t"]["players"]:
                inventory: list[Weapon] = []
                for weapon in player["inventory"] or []:
                    inventory.append(Weapon(
                        weapon_name=weapon["weaponName"],
                        weapon_class=weapon["weaponClass"],
                        ammo_in_magazine=weapon["ammoInMagazine"],
                        ammo_in_reserve=weapon["ammoInReserve"],
                    ))

                t_players.append(PlayerFrameState(
                    steam_id=player["steamID"],
                    name=player["name"],
                    team=player["team"],
                    side=player["side"],
                    x=player["x"],
                    y=player["y"],
                    z=player["z"],
                    velocity_x=player["velocityX"],
                    velocity_y=player["velocityY"],
                    velocity_z=player["velocityZ"],
                    view_x=player["viewX"],
                    view_y=player["viewY"],
                    hp=player["hp"],
                    armor=player["armor"],
                    active_weapon=player["activeWeapon"],
                    total_utility=player["totalUtility"],
                    is_alive=player["isAlive"],
                    is_blinded=player["isBlinded"],
                    is_airborne=player["isAirborne"],
                    is_ducking=player["isDucking"],
                    is_ducking_in_progress=player["isDuckingInProgress"],
                    is_unducking_in_progress=player["isUnDuckingInProgress"],
                    is_defusing=player["isDefusing"],
                    is_planting=player["isPlanting"],
                    is_reloading=player["isReloading"],
                    is_in_bomb_zone=player["isInBombZone"],
                    is_in_buy_zone=player["isInBuyZone"],
                    is_standing=player["isStanding"],
                    is_scoped=player["isScoped"],
                    is_walking=player["isWalking"],
                    is_unknown=player["isUnknown"],
                    inventory=inventory,
                    spotters=player["spotters"],
                    equipment_value=player["equipmentValue"],
                    equipment_value_freeze_time_end=player["equipmentValueFreezetimeEnd"],
                    equipment_value_round_start=player["equipmentValueRoundStart"],
                    cash=player["cash"],
                    cash_spend_this_round=player["cashSpendThisRound"],
                    cash_spend_total=player["cashSpendTotal"],
                    has_helmet=player["hasHelmet"],
                    has_defuse_kit=player["hasDefuse"],
                    has_bomb=player["hasBomb"],
                    ping=player["ping"],
                    zoom_level=player["zoomLevel"],
                ))

            t = TeamFrameState(
                side=frame["t"]["side"],
                team_name=frame["t"]["teamName"],
                team_eq_val=frame["t"]["teamEqVal"],
                alive_players=frame["t"]["alivePlayers"],
                total_utility=frame["t"]["totalUtility"],
                players=t_players,
            )

            ct: TeamFrameState
            
            ct_players: list[PlayerFrameState] = []
            for player in frame["ct"]["players"]:
                inventory: list[Weapon] = []
                for weapon in player["inventory"] or []:
                    inventory.append(Weapon(
                        weapon_name=weapon["weaponName"],
                        weapon_class=weapon["weaponClass"],
                        ammo_in_magazine=weapon["ammoInMagazine"],
                        ammo_in_reserve=weapon["ammoInReserve"],
                    ))

                ct_players.append(PlayerFrameState(
                    steam_id=player["steamID"],
                    name=player["name"],
                    team=player["team"],
                    side=player["side"],
                    x=player["x"],
                    y=player["y"],
                    z=player["z"],
                    velocity_x=player["velocityX"],
                    velocity_y=player["velocityY"],
                    velocity_z=player["velocityZ"],
                    view_x=player["viewX"],
                    view_y=player["viewY"],
                    hp=player["hp"],
                    armor=player["armor"],
                    active_weapon=player["activeWeapon"],
                    total_utility=player["totalUtility"],
                    is_alive=player["isAlive"],
                    is_blinded=player["isBlinded"],
                    is_airborne=player["isAirborne"],
                    is_ducking=player["isDucking"],
                    is_ducking_in_progress=player["isDuckingInProgress"],
                    is_unducking_in_progress=player["isUnDuckingInProgress"],
                    is_defusing=player["isDefusing"],
                    is_planting=player["isPlanting"],
                    is_reloading=player["isReloading"],
                    is_in_bomb_zone=player["isInBombZone"],
                    is_in_buy_zone=player["isInBuyZone"],
                    is_standing=player["isStanding"],
                    is_scoped=player["isScoped"],
                    is_walking=player["isWalking"],
                    is_unknown=player["isUnknown"],
                    inventory=inventory,
                    spotters=player["spotters"],
                    equipment_value=player["equipmentValue"],
                    equipment_value_freeze_time_end=player["equipmentValueFreezetimeEnd"],
                    equipment_value_round_start=player["equipmentValueRoundStart"],
                    cash=player["cash"],
                    cash_spend_this_round=player["cashSpendThisRound"],
                    cash_spend_total=player["cashSpendTotal"],
                    has_helmet=player["hasHelmet"],
                    has_defuse_kit=player["hasDefuse"],
                    has_bomb=player["hasBomb"],
                    ping=player["ping"],
                    zoom_level=player["zoomLevel"],
                ))

            ct = TeamFrameState(
                side=frame["ct"]["side"],
                team_name=frame["ct"]["teamName"],
                team_eq_val=frame["ct"]["teamEqVal"],
                alive_players=frame["ct"]["alivePlayers"],
                total_utility=frame["ct"]["totalUtility"],
                players=ct_players,
            )

            projectiles: list[Projectile] = []
            for projectile in frame["projectiles"]:
                projectiles.append(Projectile(
                    projectile_type=projectile["projectileType"],
                    x=projectile["x"],
                    y=projectile["y"],
                    z=projectile["z"],
                ))

            smokes: list[Smoke] = []
            for smoke in frame["smokes"]:
                smokes.append(Smoke(
                    grenade_entity_id=smoke["grenadeEntityID"],
                    start_tick=smoke["startTick"],
                    x=smoke["x"],
                    y=smoke["y"],
                    z=smoke["z"],
                ))

            fires: list[Fire] = []
            for fire in frame["fires"]:
                fires.append(Fire(
                    unique_id=fire["uniqueID"],
                    x=fire["x"],
                    y=fire["y"],
                    z=fire["z"],
                ))

            frames.append(Frame(
                is_kill_frame = frame["isKillFrame"],
                tick=frame["tick"],
                seconds=frame["seconds"],
                clock_time=frame["clockTime"],
                t=t,
                ct=ct,
                bomb_planted=frame["bombPlanted"],
                bomb_site=frame["bombsite"],
                bomb=Bomb(
                    x=frame["bomb"]["x"],
                    y=frame["bomb"]["y"],
                    z=frame["bomb"]["z"],
                ),
                projectiles=projectiles,
                smokes=smokes,
                fires=fires
            ))

        game_rounds.append(Round(
            round_number=round["roundNum"],
            is_warmup=round["isWarmup"],
            start_tick=round["startTick"],
            freeze_time_end_tick=round["freezeTimeEndTick"],
            end_tick=round["endTick"],
            end_official_tick=round["endOfficialTick"],
            bomb_plant_tick=round["bombPlantTick"],
            t_score=round["tScore"],
            ct_score=round["ctScore"],
            end_t_score=round["endTScore"],
            end_ct_score=round["endCTScore"],
            ct_team=round["ctTeam"],
            t_team=round["tTeam"],
            winning_side=round["winningSide"],
            winning_team=round["winningTeam"],
            losing_team=round["losingTeam"],
            round_end_reason=round["roundEndReason"],
            ct_freeze_time_end_eq_val=round["ctFreezeTimeEndEqVal"],
            ct_round_start_eq_val=round["ctRoundStartEqVal"],
            ct_round_spend_money=round["ctRoundSpendMoney"],
            ct_buy_type=round["ctBuyType"],
            t_freeze_time_end_eq_val=round["tFreezeTimeEndEqVal"],
            t_round_start_eq_val=round["tRoundStartEqVal"],
            t_round_spend_money=round["tRoundSpendMoney"],
            t_buy_type=round["tBuyType"],
            ct_side=ct_side,
            t_side=t_side,
            kills=kills,
            damages=damages,
            grenades=grenades,
            bomb_events=bomb_events,
            weapon_fires=weapon_fires,
            flashes=flashes,
            frames=frames,
        ))

    structured_demo = Demo(
        match_id=demo_file_data["matchID"],
        client_name=demo_file_data["clientName"],
        map_name=demo_file_data["mapName"],
        tick_rate=demo_file_data["tickRate"],
        playback_ticks=demo_file_data["playbackTicks"],
        playback_frames_count=demo_file_data["playbackFramesCount"],
        parsed_to_frame_index=demo_file_data["parsedToFrameIdx"],
        parser_parameters=ParserParameters(
            parse_rate=demo_file_data["parserParameters"]["parseRate"],
            do_parse_frames=demo_file_data["parserParameters"]["parseFrames"],
            do_parse_kill_frames=demo_file_data["parserParameters"]["parseKillFrames"],
            trade_time=demo_file_data["parserParameters"]["tradeTime"],
            round_buy_style=demo_file_data["parserParameters"]["roundBuyStyle"],
            are_damages_rolled_up=demo_file_data["parserParameters"]["damagesRolledUp"],
        ),
        server_vars=ServerVars(
            cash_bomb_defused=demo_file_data["serverVars"]["cashBombDefused"],
            cash_bomb_planted=demo_file_data["serverVars"]["cashBombPlanted"],
            cash_team_t_win_bomb=demo_file_data["serverVars"]["cashTeamTWinBomb"],
            cash_win_defuse=demo_file_data["serverVars"]["cashWinDefuse"],
            cash_win_time_run_out=demo_file_data["serverVars"]["cashWinTimeRunOut"],
            cash_win_elimination=demo_file_data["serverVars"]["cashWinElimination"],
            cash_player_killed_default=demo_file_data["serverVars"]["cashPlayerKilledDefault"],
            cash_team_loser_bonus=demo_file_data["serverVars"]["cashTeamLoserBonus"],
            cash_team_loser_bonus_consecutive=demo_file_data["serverVars"]["cashTeamLoserBonusConsecutive"],
            round_time=demo_file_data["serverVars"]["roundTime"],
            round_time_defuse=demo_file_data["serverVars"]["roundTimeDefuse"],
            round_restart_delay=demo_file_data["serverVars"]["roundRestartDelay"],
            freeze_time=demo_file_data["serverVars"]["freezeTime"],
            buy_time=demo_file_data["serverVars"]["buyTime"],
            bomb_timer=demo_file_data["serverVars"]["bombTimer"],
            max_rounds=demo_file_data["serverVars"]["maxRounds"],
            timeouts_allowed=demo_file_data["serverVars"]["timeoutsAllowed"],
            coaching_allowed=demo_file_data["serverVars"]["coachingAllowed"],
        ),
        match_phases=MatchPhases(
            announcement_last_round_half=demo_file_data["matchPhases"]["announcementLastRoundHalf"],
            announcement_final_round=demo_file_data["matchPhases"]["announcementFinalRound"],
            announcement_match_started=demo_file_data["matchPhases"]["announcementMatchStarted"],
            round_started=demo_file_data["matchPhases"]["roundStarted"],
            round_ended=demo_file_data["matchPhases"]["roundEnded"],
            round_freeze_time_ended=demo_file_data["matchPhases"]["roundFreezetimeEnded"],
            round_ended_official=demo_file_data["matchPhases"]["roundEndedOfficial"],
            game_half_ended=demo_file_data["matchPhases"]["gameHalfEnded"],
            match_start=demo_file_data["matchPhases"]["matchStart"],
            match_started_changed=demo_file_data["matchPhases"]["matchStartedChanged"],
            warmup_changed=demo_file_data["matchPhases"]["warmupChanged"],
            team_switch=demo_file_data["matchPhases"]["teamSwitch"],
        ),
        matchmaking_ranks=demo_file_data["matchmakingRanks"],
        player_connections=player_connections,
        game_rounds=game_rounds,
    )

    return structured_demo