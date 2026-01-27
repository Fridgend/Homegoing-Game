import pygame

import src.config as cfg

def grid_pos_to_view_pos(grid_pos: pygame.Vector2) -> pygame.Vector2:
    return grid_pos * cfg.config.tile_size


class Camera:
    def __init__(self):
        self.pos: pygame.Vector2 = pygame.Vector2(0, 0)

        self.window_center = cfg.config.window_dims // 2

    def center(self, pos: pygame.Vector2, bounds: pygame.Vector2) -> None:
        self.pos = pos - self.window_center
        self.clamp_pos(bounds)

    def clamp_pos(self, bounds: pygame.Vector2) -> None:
        self.pos.x = pygame.math.clamp(self.pos.x, 0, cfg.config.window_dims.x)
        self.pos.y = pygame.math.clamp(self.pos.y, 0, cfg.config.window_dims.y)

    def world_pos_to_view_pos(self, world_pos: pygame.Vector2) -> pygame.Vector2:
        return world_pos - self.pos