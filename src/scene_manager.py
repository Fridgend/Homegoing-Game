import json

from src.dialogue import Monologue, Dialogue, MonologueOption, MonologueLine
from src.entity import Entity
from src.entity_route import Waypoint
from src.event import *
from src.map_element import MapElement
from src.npc import NPC
from src.player import Player
from src.route_tracker import Conditions
from src.scene import Scene
from src.scene_in_out import SceneEntrance, SceneExit, str_to_scene_transition
from src.sprite import Sprite, copy_sprite
from src.trigger import Trigger
from src.ui_manager import UIManager

def parse_conditions(conditions_obj: dict) -> Conditions:
    all_flags: list[str] = [flag for flag in conditions_obj.get("all", [])]
    any_flags: list[str] = [flag for flag in conditions_obj.get("any", [])]
    not_flags: list[str] = [flag for flag in conditions_obj.get("not", [])]

    return Conditions(all_flags=all_flags, any_flags=any_flags, not_flags=not_flags)

def parse_entity_route(route_obj: dict) -> EntityRoute:
    waypoints_obj: list = route_obj.get("waypoints", [])
    waypoints: list[Waypoint] = []
    for waypoint_obj in waypoints_obj:
        face_dir: pygame.Vector2 = pygame.Vector2()
        match waypoint_obj.get("face_dir", ""):
            case "up":
                face_dir = pygame.Vector2(0, -1)
            case "down":
                face_dir = pygame.Vector2(0, 1)
            case "left":
                face_dir = pygame.Vector2(-1, 0)
            case "right":
                face_dir = pygame.Vector2(1, 0)
            case "":
                face_dir = pygame.Vector2(0, 1)

        waypoints.append(Waypoint(
            pos=pygame.Vector2(waypoint_obj.get("x", 0), waypoint_obj.get("y", 0)),
            speed=waypoint_obj.get("speed", 1),
            face_dir=face_dir,
            wait=waypoint_obj.get("wait", 0)
        ))

    conditions_obj: dict = route_obj.get("conditions", {})
    conditions: Conditions = parse_conditions(conditions_obj)

    return EntityRoute(waypoints=waypoints, conditions=conditions)

def parse_catch(catch_obj: dict) -> CatchEvent | None:
    name: str = catch_obj.get("name", "")
    match name:
        case "on_player_enter":
            rect_obj: dict = catch_obj.get("rect", {})
            event = OnPlayerEnter(
                rect=pygame.Rect(rect_obj.get("x", 0), rect_obj.get("y", 0), rect_obj.get("w", 0), rect_obj.get("h", 0))
            )
        case "on_entity_enter":
            rect_obj: dict = catch_obj.get("rect", {})
            event = OnEntityEnter(
                ids=[ind for ind in catch_obj.get("ids", [])],
                rect=pygame.Rect(rect_obj.get("x", 0), rect_obj.get("y", 0), rect_obj.get("w", 0), rect_obj.get("h", 0))
            )
        case "on_scene_load":
            event = OnSceneLoad()
        case "on_scene_enter":
            event = OnSceneStart()
        case "on_scene_exit":
            event = OnSceneExit()
        case _:
            return None

    event.conditions = parse_conditions(catch_obj.get("conditions", {}))
    return event

def parse_dispatch(dispatch_obj: dict, game) -> DispatchEvent | None:
    name: str = dispatch_obj.get("name", "")
    match name:
        case "exit_scene":
            event = ExitScene(
                transition=dispatch_obj.get("transition"),
                transition_time=dispatch_obj.get("transition_time"),
                next_scene=dispatch_obj.get("next_scene"),
                entrance=dispatch_obj.get("entrance")
            )
        case "start_running_scene":
            event = StartRunningScene(
                game=game,
                params=dispatch_obj
            )
        case "end_game":
            event = EndGame(
                game=game
            )
        case "modify_flags":
            event = ModifyFlags(
                how=dispatch_obj.get("how", ""),
                value=dispatch_obj.get("value", "")
            )
        case "add_entity":
            event = AddEntity(
                ids=[ind for ind in dispatch_obj.get("ids", [])]
            )
        case "remove_entity":
            event = RemoveEntity(
                ids=[ind for ind in dispatch_obj.get("ids", [])]
            )
        case "set_route":
            event = SetEntityRoute(
                entity_id=dispatch_obj.get("entity_id", ""),
                route_id=dispatch_obj.get("route_id", "")
            )
        case "start_entity_dialogue":
            event = BeginEntityDialogue(
                entity_id=dispatch_obj.get("entity_id", ""),
                dialogue_id=dispatch_obj.get("dialogue_id", "")
            )
        case "start_independent_dialogue":
            event = BeginIndependentDialogue(
                dialogue=parse_dialogue(
                    dialogue_obj=dispatch_obj.get("dialogue"),
                    entity_id="",
                    game=game
                )
            )
        case "end_dialogue":
            event = EndDialogueAbruptly()
        case "move_camera_to_pos":
            pos_obj: dict = dispatch_obj.get("pos", {})
            event = MoveCameraPosition(
                pos=pygame.Vector2(pos_obj.get("x", 0), pos_obj.get("y", 0)),
                duration=dispatch_obj.get("duration", 0)
            )
        case "move_camera_to_entity":
            event = MoveCameraEntity(
                entity_id=dispatch_obj.get("entity_id", ""),
                duration=dispatch_obj.get("duration", 0)
            )
        case "move_camera_follow_entity":
            event = MoveCameraFollowEntity(
                entity_id=dispatch_obj.get("entity_id", ""),
            )
        case "move_player":
            waypoints: list = dispatch_obj.get("waypoints", [])
            event = MovePlayer(
                parse_entity_route({"waypoints": waypoints})
            )
        case "reset_camera":
            event = ResetCamera()
        case "shake_camera":
            event = ShakeCamera(
                time=dispatch_obj.get("time", 0),
                intensity=dispatch_obj.get("intensity", 0)
            )
        case "stop_shake_camera":
            event = EndCameraShake()
        case "play_audio":
            event = PlayAudio(
                audio_id=dispatch_obj.get("identifier", ""),
                volume=dispatch_obj.get("volume", 0)
            )
        case "launch_script":
            event = LaunchScript(
                script_path=dispatch_obj.get("path", "")
            )
        case "show_attack_choice":
            event = ShowAttackChoice(
                peace_path=dispatch_obj.get("peace_path", ""),
                war_path=dispatch_obj.get("war_path", "")
            )
        case "enable_trigger":
            event = EnableTrigger(
                trigger_id=dispatch_obj.get("identifier", "")
            )
        case "disable_trigger":
            event = DisableTrigger(
                trigger_id=dispatch_obj.get("identifier", "")
            )
        case _:
            return None

    event.conditions = parse_conditions(dispatch_obj.get("conditions", {}))
    event.wait_for_previous = dispatch_obj.get("wait_for_previous", False)
    event.wait = dispatch_obj.get("wait", 0)
    event.org_wait = event.wait
    return event

def parse_monologue_option(option_obj: dict) -> MonologueOption:
    return MonologueOption(
        text=option_obj.get("text", ""),
        next_monologue=option_obj.get("next_monologue", ""),
        conditions=parse_conditions(option_obj.get("conditions", {}))
    )

def parse_monologue(monologue_obj: dict, game) -> Monologue:
    conditions_obj: dict = monologue_obj.get("conditions", {})
    conditions: Conditions = parse_conditions(conditions_obj)

    lines: list[MonologueLine] = []
    lines_obj: list = monologue_obj.get("lines", [])
    for line_obj in lines_obj:
        lines.append(MonologueLine(
            text=line_obj.get("text", ""),
            speed=line_obj.get("char_time", 0)
        ))

    set_route: list[tuple[str, Conditions]] = []
    set_routes_obj: list = monologue_obj.get("set_route_on_reach", [])
    for set_route_obj in set_routes_obj:
        set_route.append((
            set_route_obj.get("id", ""),
            parse_conditions(set_route_obj.get("conditions", {}))
        ))

    dispatch_events: list[DispatchEvent] = []
    dispatch_objs: list = monologue_obj.get("dispatch_on_reach", [])
    for dispatch_obj in dispatch_objs:
        de: DispatchEvent | None = parse_dispatch(dispatch_obj, game)
        if de is not None:
            dispatch_events.append(de)

    modify_flags: list[tuple[str, str]] = []
    modify_flags_objs: list = monologue_obj.get("modify_flags_on_reach", [])
    for modify_flags_obj in modify_flags_objs:
        modify_flags.append((modify_flags_obj.get("how", ""), modify_flags_obj.get("value", "")))

    options: list[MonologueOption] = []
    options_obj: list = monologue_obj.get("options", [])
    for option_obj in options_obj:
        options.append(parse_monologue_option(option_obj))

    speaker_image: pygame.Surface | None = None
    if monologue_obj.get("speaker_image", "") != "":
        speaker_image = AssetManager.get_image(monologue_obj.get("speaker_image", ""))

    speaking_sfx: pygame.mixer.Sound | None = None
    if monologue_obj.get("speaking_sfx", "") != "":
        speaking_sfx = AssetManager.get_audio(monologue_obj.get("speaking_sfx", ""))

    return Monologue(
        conditions=conditions,
        alt_monologue=monologue_obj.get("alt_monologue", ""),
        speaker=monologue_obj.get("speaker", ""),
        lines=lines,
        font=AssetManager.get_font(monologue_obj.get("font", "")),
        next_monologue=monologue_obj.get("next_monologue", None),
        set_route=set_route,
        dispatch=DispatchChain(dispatch_events),
        modify_flags=modify_flags,
        options=options,
        speaker_image=speaker_image,
        speaking_sfx=speaking_sfx
    )


def parse_dialogue(dialogue_obj: dict, entity_id: str, game) -> Dialogue:
    start_monologues: list[tuple[str, Conditions]] = []
    start_monologues_obj: list = dialogue_obj.get("start_monologue", [])
    for start_monologue_obj in start_monologues_obj:
        start_monologues.append((
            start_monologue_obj.get("id", ""),
            parse_conditions(start_monologue_obj.get("conditions", {}))
        ))

    monologues: dict[str, Monologue] = {}
    monologues_obj: list = dialogue_obj.get("monologues", [])
    for monologue_obj in monologues_obj:
        monologues[monologue_obj.get("id", "")] = parse_monologue(monologue_obj, game)

    return Dialogue(
        conditions=parse_conditions(dialogue_obj.get("conditions", {})),
        start_monologues=start_monologues,
        monologues=monologues,
        entity_id=entity_id
    )


def parse_scene(scene_obj: dict, game) -> Scene:
    void_color_obj: dict = scene_obj.get("void_color", {})
    void_color: tuple[int, int, int, int] = (
        void_color_obj.get("r", 0), void_color_obj.get("g", 0), void_color_obj.get("b", 0),
        void_color_obj.get("a", 0)
    )

    bounds_obj: dict = scene_obj.get("bounds")
    bounds = pygame.Vector2(bounds_obj.get("x", 0), bounds_obj.get("y", 0))

    background_music_obj: dict = scene_obj.get("background_music", {})
    if AssetManager.get_audio(background_music_obj.get("identifier", "")) is not None:
        background_music: pygame.mixer.Sound | None = pygame.mixer.Sound(
            AssetManager.get_audio(background_music_obj.get("identifier", "")))
        background_music.set_volume(background_music_obj.get("volume", 0))
    else:
        background_music: pygame.mixer.Sound | None = None

    map_elements_obj: list = scene_obj.get("map_elements", [])
    map_elements: list[MapElement] = []
    for map_element_obj in map_elements_obj:
        rect_obj: dict = map_element_obj.get("rect", {})
        rect: pygame.Rect = pygame.Rect(rect_obj.get("x", 0), rect_obj.get("y", 0),
                                        rect_obj.get("w", 0), rect_obj.get("h", 0))
        map_elements.append(MapElement(
            rect=rect,
            image=AssetManager.get_image(map_element_obj.get("image", "")),
            collision=map_element_obj.get("collision", False)
        ))

    entity_lookup: dict = {}
    entity_lookup_obj: list = scene_obj.get("entity_lookup", [])
    for lookup_entry_obj in entity_lookup_obj:
        sprite: Sprite = copy_sprite(AssetManager.get_sprite(lookup_entry_obj.get("sprite", "")))
        sprite.set_default_anim(lookup_entry_obj.get("default_animation", ""))
        sprite.set_frame_time(lookup_entry_obj.get("animation_frame_time", 0))

        entity_lookup[lookup_entry_obj.get("id")] = (
            sprite,
            lookup_entry_obj.get("collision", False)
        )

    player_obj: dict = scene_obj.get("player", {})
    player_fallback_spawn: dict = player_obj.get("fallback_spawn", {})
    player = Player(
        spawn=pygame.Vector2(player_fallback_spawn.get("x", 0), player_fallback_spawn.get("y", 0)),
        sprite=copy_sprite(entity_lookup.get(player_obj.get("lookup", ""))[0]),
        move_duration=player_obj.get("move_duration", 0)
    )

    triggers: dict[str, Trigger] = {}
    triggers_obj: list = scene_obj.get("triggers", [])
    for trigger_obj in triggers_obj:
        catches: list = [parse_catch(e) for e in trigger_obj.get("catch", [])]
        dispatches: list = [parse_dispatch(e, game) for e in trigger_obj.get("dispatch", [])]
        for i in range(catches.count(None)): catches.remove(None)
        for i in range(dispatches.count(None)): dispatches.remove(None)

        triggers[trigger_obj.get("identifier", "")] = Trigger(
            disabled=trigger_obj.get("disabled", False),
            once=trigger_obj.get("once", False),
            catch=catches,
            dispatch=dispatches
        )

    entrances: dict[str, SceneEntrance] = {}
    entrances_obj: list = scene_obj.get("entrances", [])
    for entrance_obj in entrances_obj:
        spawn_obj: dict = entrance_obj.get("spawn", {})
        entrances[entrance_obj.get("identifier", "")] = SceneEntrance(
            spawn=pygame.Vector2(spawn_obj.get("x", 0), spawn_obj.get("y", 0)),
            transition=str_to_scene_transition(entrance_obj.get("transition", "")),
            transition_time=entrance_obj.get("transition_time", 0)
        )

    exits: list[SceneExit] = []
    exits_obj: list = scene_obj.get("exits", [])
    for exit_obj in exits_obj:
        rect_obj: dict = exit_obj.get("rect", {})
        rect: pygame.Rect = pygame.Rect(
            rect_obj.get("x", 0), rect_obj.get("y", 0), rect_obj.get("w", 0), rect_obj.get("h", 0)
        )

        exits.append(SceneExit(
            rect=rect,
            require_interact=exit_obj.get("require_interact", False),
            transition=str_to_scene_transition(exit_obj.get("transition", "")),
            transition_time=exit_obj.get("transition_time", 0),
            next_scene=exit_obj.get("next_scene", ""),
            next_entrance=exit_obj.get("entrance", ""),
            conditions=parse_conditions(exit_obj.get("conditions", {}))
        ))

    entities: dict[str, Entity] = {}

    entities_obj: list = scene_obj.get("entities", [])
    for entity_obj in entities_obj:
        conditions_obj: dict = entity_obj.get("conditions", {})
        conditions: Conditions = parse_conditions(conditions_obj)

        dialogues: dict[str, Dialogue] = {}
        dialogues_obj: list = entity_obj.get("dialogues", [])
        for dialogue_obj in dialogues_obj:
            dialogues[dialogue_obj.get("id", "")] = parse_dialogue(dialogue_obj, entity_obj.get("id", ""), game)

        routes: dict[str, EntityRoute] = {}
        routes_obj: list = entity_obj.get("routes", [])
        for route_obj in routes_obj:
            routes[route_obj.get("id", "")] = parse_entity_route(route_obj)

        if len(dialogues) > 0:
            spawn_obj: dict = entity_obj.get("spawn", {})
            new_npc: NPC = NPC(
                sprite=copy_sprite(entity_lookup.get(entity_obj.get("lookup", ""))[0]),
                collision=entity_lookup.get(entity_obj.get("lookup", ""))[1],
                spawn=pygame.Vector2(spawn_obj.get("x", 0), spawn_obj.get("y", 0)),
                conditions=conditions,
                routes=routes,
                dialogues=dialogues
            )
            entities[entity_obj.get("id", "")] = new_npc
        else:
            spawn_obj: dict = entity_obj.get("spawn", {})
            new_entity: Entity = Entity(
                sprite=copy_sprite(entity_lookup.get(entity_obj.get("lookup", ""))[0]),
                collision=entity_lookup.get(entity_obj.get("lookup", ""))[1],
                spawn=pygame.Vector2(spawn_obj.get("x", 0), spawn_obj.get("y", 0)),
                conditions=conditions,
                routes=routes
            )
            entities[entity_obj.get("id", "")] = new_entity

    scene: Scene = Scene(
        void_color=void_color,
        bounds=bounds,
        background_music=background_music,
        map_elements=map_elements,
        player=player,
        entities=entities,
        triggers=triggers,
        entrances=entrances,
        exits=exits
    )

    return scene


class SceneManager:
    def __init__(self, scene_guide: str, game):
        self.scenes: dict[str, Scene] = {}
        self.current_scene: str = ""
        self.start_scene: str = ""

        self.fade = 0
        self.fading = 0

        self.overlay: pygame.Surface = pygame.Surface(pygame.display.get_window_size()).convert()
        self.overlay.fill((0, 0, 0))

        with open(scene_guide, "r") as file:
            obj = json.load(file)

        self.start_scene = obj.get("start_scene", "")
        for scene_obj in obj.get("scenes", []):
            with open(scene_obj.get("path"), "r") as file:
                scene_json = json.load(file)
            self.add_scene(scene_obj.get("name"), parse_scene(scene_json, game))

    def set_music_volume(self, volume: float) -> None:
        for _, scene in self.scenes.items():
            scene.set_music_volume(volume)

    def add_scene(self, name: str, scene: Scene) -> None:
        self.scenes[name] = scene

    def load_scene(self, scene_name: str, entrance_id: str, player_face_dir: pygame.Vector2,
                   from_continue: bool = False) -> None:
        same_bg_music: bool = False
        if self.current_scene != "":
            if self.scenes[self.current_scene].background_music is None or self.scenes[scene_name].background_music is None:
                same_bg_music = False
            elif self.scenes[self.current_scene].background_music.get_raw() == self.scenes[scene_name].background_music.get_raw():
                volume: float = self.scenes[scene_name].background_music.get_volume()
                self.scenes[scene_name].background_music = self.scenes[self.current_scene].background_music
                self.scenes[scene_name].background_music.set_volume(volume)
                same_bg_music = True
            self.scenes[self.current_scene].unload(same_bg_music)
        self.scenes[scene_name].load(entrance_id, player_face_dir, same_bg_music and not from_continue, from_continue)
        self.current_scene = scene_name

    def input(self, ui_manager: UIManager, keys: pygame.key.ScancodeWrapper) -> None:
        self.scenes[self.current_scene].input(ui_manager, self, keys)

    def update(self, ui_manager: UIManager, dt: float) -> None:
        self.fade = pygame.math.clamp(self.fade + self.fading * dt, 0, 255)
        self.scenes[self.current_scene].update(ui_manager, dt, self)

    def render(self, window_surface: pygame.Surface, ui_manager: UIManager) -> None:
        self.scenes[self.current_scene].render(window_surface, ui_manager)

        if self.fade > 0:
            self.overlay.set_alpha(self.fade)
            window_surface.blit(self.overlay, (0, 0))
