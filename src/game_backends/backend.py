import enum
import pygame

class GameState(enum.Enum):
    MAIN_MENU = 0
    PAUSED = 1
    PLAYING = 2
    SCENE_BUILDER = 3
    ENTITY_CONFIGURER = 4
    QUITTING = 5

class Backend:
    def __init__(self):
        self.fade: int = 0
        self.fading: int = 0
        self.overlay: pygame.Surface = pygame.Surface(pygame.display.get_window_size(), pygame.SRCALPHA)

        self.next_backend = None

    def init(self, game):
        self.fade = 0
        self.fading = 500

    def unload(self, game):
        pass

    def input(self, game):
        pass

    def update(self, game):
        pass

    def render(self, game):
        pass