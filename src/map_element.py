import pygame

from src.camera import Camera
from src.config import Config

class MapElement:
    def __init__(self, rect: pygame.Rect, image: pygame.Surface | None, collision: bool):
        self.rect: pygame.Rect = rect
        self.collision: bool = collision

        self.render_surface: pygame.Surface | None = None
        self.image_dims: pygame.Vector2 = pygame.Vector2(0, 0) if image is None else pygame.Vector2(image.get_size())

        if image is not None:
            dims: pygame.Vector2 = pygame.Vector2(image.get_size()) / Config.TILE_SIZE
            self._generate_render_surface(image, pygame.Vector2(dims.x * self.rect.w, dims.y * self.rect.h))

    def get_collision(self, rect: pygame.Rect) -> bool:
        return self.collision and rect.colliderect(self.rect)

    def render(self, surface: pygame.Surface) -> None:
        if self.render_surface is None:
            return
        centered: pygame.Vector2 = pygame.Vector2(self.rect.topleft) * Config.TILE_SIZE - self.image_dims / 2
        centered.y -= self.image_dims.y - Config.TILE_SIZE
        surface.blit(self.render_surface, Camera.world_pos_to_view_pos(centered))

    def _generate_render_surface(self, image: pygame.Surface, dims: pygame.Vector2) -> None:
        self.render_surface = pygame.Surface((dims.x * Config.TILE_SIZE, dims.y * Config.TILE_SIZE)).convert()
        for x_pos in range(int(dims.x)):
            for y_pos in range(int(dims.y)):
                self.render_surface.blit(image, (x_pos * Config.TILE_SIZE, y_pos * Config.TILE_SIZE))
