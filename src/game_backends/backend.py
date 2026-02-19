import enum
import pygame

class GameState(enum.Enum):
    MAIN_MENU = 0
    PAUSED = 1
    PLAYING = 2
    QUITTING = 3

class Backend:
    def __init__(self):
        self.fade: int = 0
        self.fading: int = 0
        self.overlay: pygame.Surface = pygame.Surface(pygame.display.get_window_size()).convert()

        self.next_backend: Backend | None = None

    def init(self, game) -> None:
        self.fade = 0
        self.fading = 500

    def unload(self, game) -> None:
        pass

    def input(self, game) -> None:
        pass

    def update(self, game) -> None:
        pass

    def render(self, game) -> None:
        pass