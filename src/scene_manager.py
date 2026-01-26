import pygame
import json

from src.scene import Scene
from src.asset_manager import AssetManager
from src.camera import Camera
from src.ui_manager import UIManager
from src.player import Player
from src.entity import Entity
from src.dialogue import Monologue, Dialogue
from src.npc import NPC


def parse_monologue(monologue_obj, asset_manager: AssetManager) -> Monologue:
    return Monologue(
        speaker=monologue_obj["speaker"],
        lines=monologue_obj["lines"],
        char_speeds=monologue_obj["char_speeds"],
        font=asset_manager.get_font(monologue_obj["font"]),
        next_monologue=None,
        options=None,
        speaker_image=None if not monologue_obj["speaker_image"] else
        asset_manager.get_image(monologue_obj["speaker_image"])
    )


def parse_dialogue(dialogue_obj, asset_manager: AssetManager) -> Dialogue:
    monologues: list[Monologue] = []
    for monologue_obj in dialogue_obj["monologues"]:
        monologues.append(parse_monologue(monologue_obj, asset_manager))

    for (monologue, obj) in zip(monologues, dialogue_obj["monologues"]):
        next_idx: int = obj.get("next_monologue")
        if next_idx is not None:
            monologue.set_next_monologue(monologues[next_idx])
        for option in obj["options"]:
            monologue.add_option_monologue(option["text"], monologues[option["leads_to"]])

    dialogue: Dialogue = Dialogue(monologues[dialogue_obj["start_monologue"]])
    return dialogue


def parse_scene(scene_obj: dict, asset_manager: AssetManager, window_surface: pygame.Surface) -> Scene:
    scene: Scene = Scene(window_surface)

    scene.clear_color = (
        scene_obj["void_color"]["r"], scene_obj["void_color"]["g"], scene_obj["void_color"]["b"],
        scene_obj["void_color"]["a"]
    )

    scene.player = Player(
        pygame.Vector2(0, 0),
        asset_manager.get_sprite(scene_obj["player"]["sprite"]), scene_obj["player"]["move_duration"])

    entity_lookup: dict = {}
    for lookup_entity in scene_obj["entity_lookup"]:
        entity_lookup[lookup_entity["name"]] = { "sprite": asset_manager.get_sprite(lookup_entity["sprite"]),
                                                 "collision": lookup_entity["has_collision"] }

    for entity in scene_obj["static_entities"]:
        new_entity: Entity = Entity(
            pygame.Vector2(entity["grid_x"], entity["grid_y"]),
            entity_lookup[entity["lookup_name"]]["sprite"],
            entity_lookup[entity["lookup_name"]]["collision"])
        scene.entities.append(new_entity)

    for npc in scene_obj["interactable_entities"]:
        dialogue: Dialogue = parse_dialogue(npc["dialogue"], asset_manager)

        new_npc: NPC = NPC(
            pygame.Vector2(npc["grid_x"], npc["grid_y"]),
            entity_lookup[npc["lookup_name"]]["sprite"],
            entity_lookup[npc["lookup_name"]]["collision"],
            dialogue
        )
        scene.entities.append(new_npc)

    return scene


class SceneManager:
    def __init__(self, scene_guide: str, asset_manager: AssetManager, window_surface: pygame.Surface):
        self.scenes: dict[str, Scene] = {}
        self.current_scene: str = ""

        with open(scene_guide, "r") as file:
            obj = json.load(file)

        for scene_obj in obj["effia"]["scenes"]:
            with open(scene_obj["path"], "r") as file:
                scene_json = json.load(file)
            self.add_scene(scene_obj["name"], parse_scene(scene_json, asset_manager, window_surface))

    def add_scene(self, name: str, scene: Scene) -> None:
        self.scenes[name] = scene

    def load_scene(self, scene_name: str) -> None:
        self.scenes[scene_name].load()
        self.current_scene = scene_name

    def input(self, ui_manager: UIManager, keys: pygame.key.ScancodeWrapper) -> None:
        self.scenes[self.current_scene].input(ui_manager, keys)

    def update(self, camera: Camera, ui_manager: UIManager, dt: float) -> None:
        self.scenes[self.current_scene].update(camera, ui_manager, dt)

    def render(self, window_surface: pygame.Surface, camera: Camera) -> None:
        self.scenes[self.current_scene].render(window_surface, camera)