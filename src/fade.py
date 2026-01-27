import pygame

class Fade:
    def __init__(self, area_dims: pygame.Vector2, init_alpha=255):
        self._fade_surface: pygame.Surface = pygame.Surface(area_dims, flags=pygame.SRCALPHA)
        self._alpha: float = init_alpha
        self._last_alpha: int = init_alpha
        self._alpha_direction: int = 0

    def update(self, dt: float) -> None:
        self._alpha += dt
        if int(self._alpha) != self._last_alpha:
            _last_alpha = int(self._alpha)
            self._fade_surface.fill((0, 0, 0, self._last_alpha))

    def begin_fade_in(self, speed: float) -> None:
        self._alpha_direction = speed

    def begin_fade_out(self, speed: float) -> None:
        self._alpha_direction = -speed

    def render_on(self, surface: pygame.Surface, pos: pygame.Vector2) -> None:
        surface.blit(self._fade_surface, pos)

    def reset(self, alpha: int) -> None:
        self._alpha = alpha
        self._last_alpha = alpha
        self._alpha_direction = 0
