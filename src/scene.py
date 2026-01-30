import pygame

from src.player import Player
from src.ui_manager import UIManager
from src.camera import Camera
from src.entity import Entity
from src.interactable import Interactable
from src.dialogue import Dialogue
import src.config as cfg

class Scene:
    def __init__(self, window_surface: pygame.Surface):
        self.clear_color: tuple = ()
        self.bounds: pygame.Vector2 = pygame.Vector2(100, 100)
        self.player: Player | None = None

        self.entities: list[Entity] = []
        self.dialogue: Dialogue | None = None

        self.clear_surface = pygame.Surface(window_surface.get_size()).convert()

    def load(self) -> None:
        self.clear_surface.fill(self.clear_color[:3])
        self.clear_surface.set_alpha(self.clear_color[3])

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
        self.player.pos.x = pygame.math.clamp(self.player.pos.x, 0, self.bounds.x * cfg.config.tile_size - self.player.sprite.dimensions.x)
        self.player.pos.y = pygame.math.clamp(self.player.pos.y, 0, self.bounds.y * cfg.config.tile_size - self.player.sprite.dimensions.y)

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
        window_surface.blit(self.clear_surface, (0, 0))
        for entity in self.entities: entity.render(window_surface, camera)
        self.player.render(window_surface, camera)

        if self.dialogue is not None:
            dims: pygame.Rect = pygame.Rect(
                cfg.config.dialogue_box_pos.x, cfg.config.dialogue_box_pos.y,
                cfg.config.dialogue_box_dims.x, cfg.config.dialogue_box_dims.y
            )

            self.dialogue.render(window_surface, dims, ui_manager)
