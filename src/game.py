import sys

import pygame

from src.asset_manager import AssetManager
from src.camera import Camera
from src.config import Config
from src.game_backends.backend import GameState, Backend
from src.game_backends.main_menu import MainMenuBackend
from src.game_backends.paused import PausedBackend
from src.game_backends.playing import PlayingBackend
from src.scene_manager import SceneManager
from src.ui_manager import UIManager


class Game:
    def __init__(self, asset_guide: str, scene_guide: str, config_path: str,
                 game_state: GameState = GameState.MAIN_MENU):
        self.running: bool = True
        Config.load(config_path)

        self.window_surface: pygame.Surface = pygame.display.set_mode(
            Config.WINDOW_DIMS, pygame.FULLSCREEN if Config.WINDOW_FULLSCREEN else 0)
        pygame.display.set_caption("Homegoing")
        Config.set_window_dimensions(self.window_surface.get_size())
        Camera.init_window_center()

        self.asset_manager: AssetManager = AssetManager(asset_guide)
        AssetManager.NULL_IMAGE = AssetManager.get_image("null")
        self.scene_manager: SceneManager = SceneManager(scene_guide)
        self.ui_manager: UIManager = UIManager(self.window_surface)
        
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.delta_time: float = 0

        self.state: GameState = game_state
        self.state_backends: dict = {
            GameState.MAIN_MENU: MainMenuBackend(),
            GameState.PAUSED: PausedBackend(),
            GameState.PLAYING: PlayingBackend()
        }
        self.backend: Backend | None = None
        self.next_backend: Backend | None = None
        self.set_backend(self.state)

    def set_backend(self, state: GameState) -> None:
        if state == GameState.QUITTING:
            self.running = False
            return
        self.next_backend = self.state_backends[state]
        self.state = state

    def run(self, FPS: int) -> None:
        while self.running:
            self.delta_time = self.clock.tick(FPS) / 1000.0

            if self.backend != self.next_backend:
                if self.backend: self.backend.unload(self)
                self.backend = self.next_backend
                self.backend.init(self)

            self.backend.input(self)
            self.backend.update(self)
            self.backend.render(self)

        pygame.quit()
        sys.exit()
