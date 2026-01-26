import pygame

from src.entity import Entity
from src.camera import Camera
from src.sprite import Sprite
from src.sprite import dir_to_str
from src.ui_manager import UIManager

class Player(Entity):
    def __init__(self, grid_pos: pygame.Vector2, sprite: Sprite, move_duration: float):
        super().__init__(grid_pos, sprite, False)

        self.pos: pygame.Vector2 = grid_pos * 32
        self.moving: bool = False
        self.move_dir: pygame.Vector2 = pygame.Vector2(0, 0)
        self.move_time: float = 0.0
        self.move_duration: float = move_duration

    def set_sprite(self, sprite: Sprite, hit_box: pygame.Vector2):
        self.sprite = sprite
        self.hit_box = hit_box
        self.pos = self.grid_pos * 32

    def input(self, keys: pygame.key.ScancodeWrapper):
        if self.moving:
            return
        
        dx: int = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy: int = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])

        if dx != 0:
            dy = 0

        if dx != 0 or dy != 0:
            self.move_dir = pygame.Vector2(dx, dy)
            self.facing = self.move_dir
            self.moving = True
            self.move_time = 0.0

    def update(self, entities: list[Entity], ui_manager: UIManager, dt: float):
        if not self.moving:
            return

        self.sprite.update(dt)

        target_grid_pos: pygame.Vector2 = self.grid_pos + self.move_dir
        for entity in entities:
            if entity.get_collision(target_grid_pos):
                self.moving = False
                self.move_dir = pygame.Vector2(0, 0)
                self.move_time = 0
                return
        
        self.move_time += dt
        t: float = min(self.move_time / self.move_duration, 1.0)

        start_pos: pygame.Vector2 = self.grid_pos * 32
        target_pos: pygame.Vector2 = target_grid_pos * 32

        self.pos = start_pos.lerp(target_pos, t)

        if t >= 1.0:
            self.grid_pos += self.move_dir
            self.moving = False

    def render(self, surface: pygame.Surface, camera: Camera):
        centered: pygame.Vector2 = self.pos - self.sprite.dimensions / 2
        surface.blit(self.sprite.get(dir_to_str(self.facing)), camera.world_pos_to_view_pos(centered))