import pygame

from src.player import Player
from src.ui_manager import UIManager
from src.asset_manager import AssetManager
from src.camera import Camera
from src.entity import Entity
from src.interactable import Interactable

class Scene:
    def __init__(self, window_surface: pygame.Surface):
        self.bounds: pygame.Vector2 = pygame.Vector2(10000, 10000)
        self.entities: list[Entity] = []

        self.clear_color: tuple = ()

        self.player: Player | None = None

        self.clear_surface = pygame.Surface(window_surface.get_size()).convert()

    def load(self) -> None:
        self.clear_surface.fill(self.clear_color[:3])
        self.clear_surface.set_alpha(self.clear_color[3])

    def input(self, ui_manager: UIManager, keys: pygame.key.ScancodeWrapper) -> None:
        if ui_manager.is_in_dialogue():
            ui_manager.input(keys)
            return

        self.player.input(keys)

        if not (keys[pygame.K_SPACE] or keys[pygame.K_RETURN]): return
        for entity in self.entities:
            entity.input(keys)
            if isinstance(entity, Interactable) and entity.can_interact(self.player):
                entity.interact(self.player, ui_manager)

    def update(self, camera: Camera, ui_manager: UIManager, dt: float) -> None:
        camera.center(self.player.pos, self.bounds)

        self.player.update(self.entities, ui_manager, dt)
        self.player.grid_pos.x = max(0, min(self.player.grid_pos.x, self.bounds.x))
        self.player.grid_pos.y = max(0, min(self.player.grid_pos.y, self.bounds.y))
        self.player.pos.x = max(0, min(self.player.pos.x, self.bounds.x - self.player.sprite.dimensions.x))
        self.player.pos.y = max(0, min(self.player.pos.y, self.bounds.y - self.player.sprite.dimensions.y))

        ui_manager.update(dt)

        for entity in self.entities: entity.update(ui_manager, dt)

    def render(self, window_surface: pygame.Surface, camera: Camera) -> None:
        window_surface.fill((0, 0, 0))
        window_surface.blit(self.clear_surface, (0, 0))
        for entity in self.entities: entity.render(window_surface, camera)
        self.player.render(window_surface, camera)