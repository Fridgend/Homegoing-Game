import pygame

from src.game_backends.backend import Backend

class PausedBackend(Backend):
    def __init__(self):
        super().__init__()
        pass

    def init(self, game):
        self.next_backend = None
        self.fade = 0
        self.fading = 500

        self.text = game.asset_manager.get_font("snake64").render("Press any key to start", True, (255, 255, 255))
        self.rect = self.text.get_rect(center=game.window_surface.get_rect().center)
        self.text2 = game.asset_manager.get_font("snake46").render("ESC to exit", True, (255, 255, 255))
        self.rect2 = self.text2.get_rect(center=game.window_surface.get_rect().center + pygame.Vector2(0, 70))
        self.text2.set_alpha(50)

    def input(self, game):
        pass

    def update(self, game):
        pass

    def render(self, game):
        pass