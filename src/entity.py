import pygame

from src.camera import Camera
from src.ui_manager import UIManager
from src.sprite import Sprite

class Entity:
    def __init__(self, grid_pos: pygame.Vector2, sprite: Sprite, collision: bool):
        self.grid_pos: pygame.Vector2 = grid_pos
        self.facing: pygame.Vector2 = pygame.Vector2(0, 1)
        self.velocity: pygame.Vector2 = pygame.Vector2(0, 0)

        self.sprite = sprite
        self.hit_box: pygame.Vector2 = self.sprite.dimensions / 32 # MAKE DYNAMIC (LARGE CHARACTERS ARENT COLLIDED WITH)

        self.collision: bool = collision

    def set_sprite(self, sprite: Sprite):
        self.sprite = sprite

    def get_collision(self, pos: pygame.Vector2) -> bool:
        return self.collision and \
               self.grid_pos.x <= pos.x < self.grid_pos.x + self.hit_box.x and \
               self.grid_pos.y <= pos.y < self.grid_pos.y + self.hit_box.y

    def look_at(self, grid_pos: pygame.Vector2):
        diff: pygame.Vector2 = self.grid_pos - grid_pos
        if abs(diff[1]) > abs(diff[0]):
            self.facing = diff[1] / abs(diff[1])
        else:
            self.facing = diff[0] / abs(diff[0])

    def input(self, keys: pygame.key.ScancodeWrapper):
        pass

    def update(self, ui_manager: UIManager, dt: float):
        pass

    def render(self, surface: pygame.Surface, camera: Camera):
        centered: pygame.Vector2 = self.grid_pos * 32 - self.sprite.dimensions / 2
        centered.x -= self.sprite.dimensions.y - 32
        surface.blit(self.sprite.get(self.facing), camera.world_pos_to_view_pos(centered))