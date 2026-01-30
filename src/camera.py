import pygame
import random

import src.config as cfg

def grid_pos_to_view_pos(grid_pos: pygame.Vector2) -> pygame.Vector2:
    return grid_pos * cfg.config.tile_size


class Camera:
    def __init__(self):
        self.pos: pygame.Vector2 = pygame.Vector2(0, 0)

        self.window_dimensions = cfg.config.window_dims
        self.window_center = cfg.config.window_dims // 2

        self.shake_offset: pygame.Vector2 = pygame.Vector2(0, 0)
        self.shake_amount: pygame.Vector2 = pygame.Vector2(0, 0)
        self.shake_duration: float = 0

        self.zoom_level: float = 1

    def center_at(self, pos: pygame.Vector2, bounds: pygame.Vector2) -> None:
        self.pos = pos - self.window_center
        self.clamp_pos(bounds)

    def clamp_pos(self, bounds: pygame.Vector2) -> None:
        self.pos.x = pygame.math.clamp(self.pos.x, 0, (bounds.x - 1) * cfg.config.tile_size - cfg.config.window_dims.x)
        self.pos.y = pygame.math.clamp(self.pos.y, 0, (bounds.y - 1) * cfg.config.tile_size - cfg.config.window_dims.y)

    def update(self, dt: float) -> None:
        self.shake_offset = self._get_shake_offset(dt)

    def world_pos_to_view_pos(self, world_pos: pygame.Vector2) -> pygame.Vector2:
        return world_pos - self.pos + self.shake_offset
            
    def shake_camera(self, intensity_x=10, intensity_y=10, duration=0.5) -> None:
        self.shake_amount.x = intensity_x
        self.shake_amount.y = intensity_y
        self.shake_duration = duration 

    def _get_shake_offset(self, dt: float) -> pygame.Vector2:
        if self.shake_duration > 0:
            fraction = self.shake_duration / max(self.shake_duration + dt, 0.01)
            current_x = self.shake_amount.x * fraction
            current_y = self.shake_amount.y * fraction
            offset_x = random.uniform(-current_x, current_x)
            offset_y = random.uniform(-current_y, current_y)
            
            self.shake_duration -= dt 
            return pygame.Vector2(offset_x, offset_y)
        
        self.shake_amount.x = 0
        self.shake_amount.y = 0
        return pygame.Vector2(0, 0)
