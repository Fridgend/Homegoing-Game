import pygame

from src.player import Player
from src.ui_manager import UIManager
from src.camera import Camera
from src.entity import Entity
from src.interactable import Interactable
from src.dialogue import Dialogue

from src.config import Config

BACKGROUND_MUSIC_FADE_MS = 1000

class Scene:
    def __init__(self, void_color: tuple[int, int, int, int], bounds: pygame.Vector2,
                 background_music: pygame.mixer.Sound
                 ):
        self.void_color: tuple[int, int, int, int] = void_color
        self.background_music: pygame.mixer.Sound = background_music
        self.bounds: pygame.Vector2 = bounds

        self.player: Player | None = None
        self.entities: list[Entity] = []
        self.dialogue: Dialogue | None = None

        self.loaded: bool = False
        self.void_surface = pygame.Surface(Config.WINDOW_DIMS).convert()
        self.void_surface.fill(self.void_color[:3])
        self.void_surface.set_alpha(self.void_color[3])

    def load(self) -> None:
        if self.loaded: return
        self.loaded = True
        self.background_music.play(loops=-1, fade_ms=BACKGROUND_MUSIC_FADE_MS)

    def unload(self) -> None:
        if not self.loaded: return
        self.loaded = False
        self.background_music.fadeout(BACKGROUND_MUSIC_FADE_MS)

    def input(self, ui_manager: UIManager, keys: pygame.key.ScancodeWrapper) -> None:
        if self.dialogue is not None:
            self.dialogue.input(keys)
            ui_manager.input(keys)
            return

        self.player.input(keys)

        if not (keys[pygame.K_SPACE] or keys[pygame.K_RETURN]): return
        for entity in self.entities:
            entity.input(keys)
            if isinstance(entity, Interactable) and entity.can_interact(self.player):
                self.dialogue = entity.interact(self.player, ui_manager)

    def update(self, camera: Camera, ui_manager: UIManager, dt: float) -> None:
        camera.center_at(self.player.pos, self.bounds)

        self.player.update(self.entities, ui_manager, dt)
        self.player.grid_pos.x = pygame.math.clamp(self.player.grid_pos.x, 0, self.bounds.x)
        self.player.grid_pos.y = pygame.math.clamp(self.player.grid_pos.y, 0, self.bounds.y)
        self.player.pos.x = pygame.math.clamp(self.player.pos.x, 0,
                                              self.bounds.x * Config.TILE_SIZE - self.player.sprite.dimensions.x)
        self.player.pos.y = pygame.math.clamp(self.player.pos.y, 0,
                                              self.bounds.y * Config.TILE_SIZE - self.player.sprite.dimensions.y)

        if self.dialogue is not None:
            self.dialogue.update(ui_manager, dt)
            if self.dialogue.fade == 0:
                self.dialogue.reset()
                self.dialogue = None

        ui_manager.update()

        for entity in self.entities:
            entity.update(ui_manager, dt)

    def render(self, window_surface: pygame.Surface, camera: Camera, ui_manager: UIManager) -> None:
        window_surface.fill((0, 0, 0))
        window_surface.blit(self.void_surface, (0, 0))
        for entity in self.entities: entity.render(window_surface, camera)
        self.player.render(window_surface, camera)

        if self.dialogue is not None:
            dims: pygame.Rect = pygame.Rect(
                Config.DIALOGUE_BOX_POS.x, Config.DIALOGUE_BOX_POS.y,
                Config.DIALOGUE_BOX_DIMS.x, Config.DIALOGUE_BOX_DIMS.y
            )

            self.dialogue.render(window_surface, dims, ui_manager)
