import pygame

from src.game_backends.backend import Backend, GameState

class MainMenuBackend(Backend):
    def __init__(self):
        super().__init__()

        self.text = None
        self.rect = None
        self.text2 = None
        self.rect2 = None

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
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game.running = False
                    return
                self.fading = -500
                self.next_backend = GameState.PLAYING

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.fading = -500
                self.next_backend = GameState.PLAYING

    def update(self, game):
        self.fade = max(0, min(255, int(self.fade + self.fading * game.delta_time)))
        if self.next_backend and self.fade == 0: game.set_backend(self.next_backend)

    def render(self, game):
        game.window_surface.fill((0, 0, 0))
        game.window_surface.blit(self.text, self.rect)
        game.window_surface.blit(self.text2, self.rect2)
        if self.fade != 0: self.overlay.fill((0, 0, 0, 255 - self.fade))
        game.window_surface.blit(self.overlay, game.window_surface.get_rect())
        pygame.display.flip()