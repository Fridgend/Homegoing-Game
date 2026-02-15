import random

import pygame

from src.config import Config


class Camera:
    POS: pygame.Vector2 = pygame.Vector2(0, 0)
    WINDOW_CENTER: pygame.Vector2 = pygame.Vector2(0, 0)

    SHAKE_OFFSET: pygame.Vector2 = pygame.Vector2(0, 0)
    SHAKE_AMOUNT: pygame.Vector2 = pygame.Vector2(0, 0)
    SHAKE_DURATION: float = 0

    TRACK = None

    @classmethod
    def init_window_center(cls) -> None:
        cls.WINDOW_CENTER = Config.WINDOW_DIMS // 2

    @classmethod
    def center_at(cls, pos: pygame.Vector2, bounds: pygame.Vector2) -> None:
        cls.POS = pos - cls.WINDOW_CENTER
        cls.clamp_pos(bounds)
        cls.POS += cls.SHAKE_OFFSET

    @classmethod
    def clamp_pos(cls, bounds: pygame.Vector2) -> None:
        max_x = max(0, (bounds.x - 1) * Config.TILE_SIZE - Config.WINDOW_DIMS.x)
        max_y = max(0, (bounds.y - 1) * Config.TILE_SIZE - Config.WINDOW_DIMS.y)
        cls.POS.x = pygame.math.clamp(cls.POS.x, 0, max_x)
        cls.POS.y = pygame.math.clamp(cls.POS.y, 0, max_y)

    @classmethod
    def update(cls, bounds: pygame.Vector2, dt: float) -> None:
        cls.SHAKE_OFFSET = cls._get_shake_offset(dt)
        if cls.TRACK is not None:
            cls.center_at(cls.TRACK.pos, bounds)

    @classmethod
    def world_pos_to_view_pos(cls, world_pos: pygame.Vector2) -> pygame.Vector2:
        return world_pos - cls.POS

    @classmethod
    def shake_camera(cls, intensity_x=3, intensity_y=3, duration=0.5) -> None:
        cls.SHAKE_AMOUNT.x = intensity_x
        cls.SHAKE_AMOUNT.y = intensity_y
        cls.SHAKE_DURATION = duration

    @classmethod
    def _get_shake_offset(cls, dt: float) -> pygame.Vector2:
        if cls.SHAKE_DURATION > 0:
            offset_x = random.uniform(-cls.SHAKE_AMOUNT.x, cls.SHAKE_AMOUNT.x)
            offset_y = random.uniform(-cls.SHAKE_AMOUNT.y, cls.SHAKE_AMOUNT.y)
            
            cls.SHAKE_DURATION -= dt
            return pygame.Vector2(offset_x, offset_y)
        
        cls.SHAKE_AMOUNT = pygame.Vector2(0, 0)
        return pygame.Vector2(0, 0)
