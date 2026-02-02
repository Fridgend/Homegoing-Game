import json

import pygame

from src.asset_manager import AssetManager
from src.camera import Camera
from src.dialogue import Monologue, Dialogue
from src.entity import Entity
from src.map_element import MapElement
from src.npc import NPC
from src.player import Player
from src.route_tracker import Conditions
from src.scene import Scene
from src.scene_in_out import SceneEntrance, SceneExit, str_to_scene_transition
from src.sprite import Sprite, copy_sprite
from src.ui_manager import UIManager


def parse_conditions(conditions_obj: dict) -> Conditions:
    all_flags: list[str] = [flag for flag in conditions_obj.get("all", [])]
    any_flags: list[str] = [flag for flag in conditions_obj.get("any", [])]
    not_flags: list[str] = [flag for flag in conditions_obj.get("not", [])]

    return Conditions(all_flags=all_flags, any_flags=any_flags, not_flags=not_flags)

def parse_monologue(monologue_obj: dict) -> Monologue:
    return Monologue(
        speaker=monologue_obj.get("speaker", ""),
        lines=monologue_obj.get("lines", []),
        char_speeds=monologue_obj.get("char_speeds", []),
        font=AssetManager.get_font(monologue_obj.get("font", "")),
        next_monologue=None,
        options=None,
        speaker_image=None if not monologue_obj.get("speaker_image", "") else
        AssetManager.get_image(monologue_obj.get("speaker_image", ""))
    )


def parse_dialogue(dialogue_obj: dict) -> Dialogue:

    monologues: list[Monologue] = []
    for monologue_obj in dialogue_obj["monologues"]:
        monologues.append(parse_monologue(monologue_obj))

    for (monologue, obj) in zip(monologues, dialogue_obj["monologues"]):
        next_idx: int = obj.get("next_monologue")
        if next_idx is not None:
            monologue.set_next_monologue(monologues[next_idx])
        for option in obj["options"]:
            monologue.add_option_monologue(option["text"], monologues[option["leads_to"]])

    dialogue: Dialogue = Dialogue(monologues[dialogue_obj["start_monologue"]])
    return dialogue


def parse_scene(scene_obj: dict) -> Scene:
    void_color_obj: dict = scene_obj.get("void_color", {})
    void_color: tuple[int, int, int, int] = (
        void_color_obj.get("r", 0), void_color_obj.get("g", 0), void_color_obj.get("b", 0),
        void_color_obj.get("a", 0)
    )

    bounds_obj: dict = scene_obj.get("bounds")
    bounds = pygame.Vector2(bounds_obj.get("x", 0), bounds_obj.get("y", 0))

    background_music_obj: dict = scene_obj.get("background_music", {})
    background_music: pygame.mixer.Sound = AssetManager.get_audio(background_music_obj.get("identifier", ""))
    background_music.set_volume(background_music_obj.get("volume", 1))

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
        grid_pos=pygame.Vector2(player_fallback_spawn.get("x", 0), player_fallback_spawn.get("y", 0)),
        sprite=copy_sprite(entity_lookup.get(player_obj.get("lookup", ""))[0]),
        move_duration=player_obj.get("move_duration", 0)
    )

    entrances: dict[str, SceneEntrance] = {}
    entrances_obj: list = scene_obj.get("entrances", [])
    for entrance_obj in entrances_obj:
        rect_obj: dict = entrance_obj.get("rect", {})
        rect: pygame.Rect = pygame.Rect(rect_obj.get("x", 0), rect_obj.get("y", 0), rect_obj.get("w", 0), rect_obj.get("h", 0))

        p_map_elements: list[MapElement] = []
        for element in map_elements:
            if element.rect.colliderect(rect):
                p_map_elements.append(element)

        scene_map_elements: list[MapElement] = []
        for x in range(rect.x, rect.x + rect.w):
            for y in range(rect.y, rect.y + rect.h):
                next_rect: pygame.Rect = pygame.Rect(x, y, 1, 1)
                for elem in p_map_elements:
                    if elem.rect.colliderect(next_rect):
                        scene_map_elements.append(MapElement(
                            rect=next_rect,
                            image=elem.render_surface.subsurface((0, 0), elem.dims * Config.TILE_SIZE),
                            collision=elem.collision
                        ))

        spawn_obj: dict = entrance_obj.get("spawn", {})
        entrances[entrance_obj.get("identifier", "")] = SceneEntrance(
            rect=rect,
            elements=scene_map_elements,
            spawn=pygame.Vector2(spawn_obj.get("x", 0), spawn_obj.get("y", 0)),
            transition=str_to_scene_transition(entrance_obj.get("transition", "")),
            transition_time=entrance_obj.get("transition_time", 0)
        )

    exits: list[SceneExit] = []
    exits_obj: list = scene_obj.get("exits", [])
    for exit_obj in exits_obj:
        rect_obj: dict = exit_obj.get("rect", {})
        rect: pygame.Rect = pygame.Rect(rect_obj.get("x", 0), rect_obj.get("y", 0), rect_obj.get("w", 0), rect_obj.get("h", 0))

        p_map_elements: list[MapElement] = []
        for element in map_elements:
            if element.rect.colliderect(rect):
                p_map_elements.append(element)

        scene_map_elements: list[MapElement] = []
        for x in range(rect.x, rect.x + rect.w):
            for y in range(rect.y, rect.y + rect.h):
                next_rect: pygame.Rect = pygame.Rect(x, y, 1, 1)
                for elem in p_map_elements:
                    if elem.rect.colliderect(next_rect):
                        scene_map_elements.append(MapElement(
                            rect=next_rect,
                            image=elem.render_surface.subsurface((0, 0), elem.image_dims),
                            collision=elem.collision
                        ))

        exits.append(SceneExit(
            rect=rect,
            elements=scene_map_elements,
            require_interact=exit_obj.get("require_interact", False),
            transition=str_to_scene_transition(exit_obj.get("transition", "")),
            transition_time=exit_obj.get("transition_time", 0),
            next_scene=exit_obj.get("next_scene", ""),
            next_entrance=exit_obj.get("entrance", ""),
            conditions=parse_conditions(exit_obj.get("conditions", {}))
        ))

    scene: Scene = Scene(
        void_color=void_color,
        bounds=bounds,
        background_music=background_music,
        map_elements=map_elements,
        player=player,
        entrances=entrances,
        exits=exits
    )

    for entity in scene_obj["static_entities"]:
        new_entity: Entity = Entity(
            pygame.Vector2(entity["grid_x"], entity["grid_y"]),
            copy_sprite(entity_lookup[entity["lookup_name"]][0]),
            entity_lookup[entity["lookup_name"]][1])
        scene.entities.append(new_entity)

    for npc in scene_obj["interactable_entities"]:
        dialogue: Dialogue = parse_dialogue(npc["dialogue"])

        new_npc: NPC = NPC(
            pygame.Vector2(npc["grid_x"], npc["grid_y"]),
            copy_sprite(entity_lookup[npc["lookup_name"]][0]),
            entity_lookup[npc["lookup_name"]][1],
            dialogue
        )
        scene.entities.append(new_npc)

    return scene


class SceneManager:
    def __init__(self, scene_guide: str):
        self.scenes: dict[str, Scene] = {}
        self.current_scene: str = ""

        self.fade = 0
        self.fading = 0

        self.overlay: pygame.Surface = pygame.Surface(pygame.display.get_window_size()).convert()
        self.overlay.fill((0, 0, 0))

        with open(scene_guide, "r") as file:
            obj = json.load(file)

        for scene_obj in obj.get("effia", {}).get("scenes", []):
            with open(scene_obj.get("path"), "r") as file:
                scene_json = json.load(file)
            self.add_scene(scene_obj.get("name"), parse_scene(scene_json))

    def add_scene(self, name: str, scene: Scene) -> None:
        self.scenes[name] = scene

    def load_scene(self, scene_name: str, entrance_id: str, player_face_dir: pygame.Vector2) -> None:
        if self.current_scene != "":
            self.scenes[self.current_scene].unload()
        self.scenes[scene_name].load(entrance_id, player_face_dir)
        self.current_scene = scene_name

    def input(self, ui_manager: UIManager, keys: pygame.key.ScancodeWrapper) -> None:
        self.scenes[self.current_scene].input(ui_manager, keys)

    def update(self, camera: Camera, ui_manager: UIManager, dt: float) -> None:
        self.fade = pygame.math.clamp(self.fade + self.fading * dt, 0, 255)
        self.scenes[self.current_scene].update(camera, ui_manager, dt, self)

    def render(self, window_surface: pygame.Surface, camera: Camera, ui_manager: UIManager) -> None:
        self.scenes[self.current_scene].render(window_surface, camera, ui_manager)

        if self.fade > 0:
            self.overlay.set_alpha(self.fade)
            window_surface.blit(self.overlay, (0, 0))
