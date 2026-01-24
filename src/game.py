import pygame
import sys
import enum

from src.scene_manager import SceneManager
from src.asset_manager import AssetManager
from src.ui_manager import UIManager
from src.camera import Camera

from src.game_backends.main_menu import MainMenuBackend
from src.game_backends.playing import PlayingBackend
from src.game_backends.paused import PausedBackend
from src.game_backends.scene_builder import SceneBuilderBackend
from src.game_backends.entity_configurer import EntityConfigurerBackend

class GameState(enum.Enum):
    MAIN_MENU = 0
    PAUSED = 1
    PLAYING = 2
    SCENE_BUILDER = 3
    ENTITY_CONFIGURER = 4

class Game:
    def __init__(self, asset_guide: str, game_state: GameState = GameState.PLAYING): # FIX: SHOULD START AT MAIN MENU
        self.running: bool = True

        self.scene_manager: SceneManager = SceneManager()
        self.asset_manager: AssetManager = AssetManager(asset_guide)

        self.window_surface: pygame.Surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.window_dimensions: pygame.Vector2 = pygame.Vector2(
            self.window_surface.get_width(), self.window_surface.get_height())
        pygame.display.set_caption("Homegoing")

        self.ui_manager: UIManager = UIManager(self.window_dimensions, self.window_surface)
        
        self.camera: Camera = Camera(self.window_dimensions, 32)
        
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.delta_time: float = 0

        self.state = game_state
        self.state_backends = [MainMenuBackend(), PausedBackend(), PlayingBackend(),
                               SceneBuilderBackend(), EntityConfigurerBackend()]
        self.backend = None
        self.next_backend = None
        self.set_backend(self.state)

    def set_backend(self, state: GameState):
        self.next_backend = self.state_backends[state.value]
        self.state = state
        self.next_backend.init(self)

    def run(self, FPS: int, FPS_warn: int):
        while self.running:
            self.delta_time = self.clock.tick(FPS) / 1000.0

            self.backend = self.next_backend

            self.backend.input(self)
            self.backend.update(self)
            self.backend.render(self)

            fps: float = self.clock.get_fps()
            if fps < FPS_warn: print("LAG SPIKE DETECTED:", fps, "FPS")

        pygame.quit()
        sys.exit()