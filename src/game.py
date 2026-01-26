import pygame
import sys

import src.config as cfg

from src.scene_manager import SceneManager
from src.asset_manager import AssetManager
from src.ui_manager import UIManager
from src.camera import Camera

from src.game_backends.main_menu import MainMenuBackend
from src.game_backends.playing import PlayingBackend
from src.game_backends.paused import PausedBackend
from src.game_backends.scene_builder import SceneBuilderBackend
from src.game_backends.entity_configurer import EntityConfigurerBackend
from src.game_backends.backend import GameState

class Game:
    def __init__(self, asset_guide: str, scene_guide: str, config_path: str, game_state: GameState = GameState.MAIN_MENU):
        self.running: bool = True
        cfg.config = cfg.Config(config_path)

        self.window_surface: pygame.Surface = pygame.display.set_mode(
            cfg.config.window_dims, pygame.FULLSCREEN if cfg.config.window_fullscreen else 0)
        pygame.display.set_caption("Homegoing")
        cfg.config.set_window_dimensions(self.window_surface.get_size())

        self.asset_manager: AssetManager = AssetManager(asset_guide)
        self.scene_manager: SceneManager = SceneManager(scene_guide, self.asset_manager, self.window_surface)
        self.ui_manager: UIManager = UIManager(self.window_surface)
        
        self.camera: Camera = Camera()
        
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.delta_time: float = 0

        self.state = game_state
        self.state_backends: dict = {
            GameState.MAIN_MENU: MainMenuBackend(),
            GameState.PAUSED: PausedBackend(),
            GameState.PLAYING: PlayingBackend(),
            GameState.SCENE_BUILDER: SceneBuilderBackend(),
            GameState.ENTITY_CONFIGURER: EntityConfigurerBackend()
        }
        self.backend = None
        self.next_backend = None
        self.set_backend(self.state)

    def set_backend(self, state: GameState):
        if state == GameState.QUITTING:
            self.running = False
            return
        self.next_backend = self.state_backends[state]
        self.state = state

    def run(self, FPS: int, FPS_warn: int):
        while self.running:
            self.delta_time = self.clock.tick(FPS) / 1000.0

            if self.backend != self.next_backend:
                if self.backend: self.backend.unload(self)
                self.backend = self.next_backend
                self.backend.init(self)

            self.backend.input(self)
            self.backend.update(self)
            self.backend.render(self)

            fps: float = self.clock.get_fps()
            if fps < FPS_warn: print("LAG SPIKE DETECTED:", fps, "FPS")

        pygame.quit()
        sys.exit()