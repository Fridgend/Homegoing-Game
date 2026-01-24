import pygame

from src.scenes.scene import Scene
from src.asset_manager import AssetManager
from src.camera import Camera
from src.ui_manager import UIManager

import os

class SceneManager:
    def __init__(self):
        self.scenes: dict[str, Scene] = {}
        self.current_scene: str = ""

    def add_scene(self, name: str, scene: Scene) -> None:
        self.scenes[name] = scene

    def load_scene(self, scene_name: str, asset_manager: AssetManager) -> None:
        self.scenes[scene_name].load(asset_manager)
        self.current_scene = scene_name

    def input(self, ui_manager: UIManager, keys: pygame.key.ScancodeWrapper) -> None:
        self.scenes[self.current_scene].input(ui_manager, keys)

    def update(self, camera: Camera, ui_manager: UIManager, dt: float) -> None:
        self.scenes[self.current_scene].update(camera, ui_manager, dt)

    def render(self, window_surface: pygame.Surface, camera: Camera) -> None:
        self.scenes[self.current_scene].render(window_surface, camera)