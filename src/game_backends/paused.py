import pygame

from src.game_backends.backend import Backend, GameState
from src.ui_manager import Text, Button

class PausedBackend(Backend):
    def __init__(self):
        super().__init__()

        self.center_pos = self.bottom_pos = self.top_pos = None

    def init(self, game):
        self.next_backend = None
        self.fade = 0
        self.fading = 500

        self.center_pos = game.window_surface.get_rect().center
        self.bottom_pos = game.window_surface.get_rect().midbottom
        self.top_pos = game.window_surface.get_rect().midtop

        game.ui_manager.add_button(Button(Text("Continue", [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(0, -70), True, game.asset_manager.get_font("snake64")
        ), pygame.Vector2(-40, 0), game.asset_manager.get_font("snake40"), [150, 0, 150, 255]))

        game.ui_manager.add_button(Button(Text("Exit to Main Menu", [255, 255, 255, 255],
            self.center_pos, True, game.asset_manager.get_font("snake64")
        ), pygame.Vector2(-40, 0), game.asset_manager.get_font("snake40"), [150, 0, 150, 255]))

        game.ui_manager.add_button(Button(Text("Exit to Desktop", [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(0, 70), True, game.asset_manager.get_font("snake64")
        ), pygame.Vector2(-40, 0), game.asset_manager.get_font("snake40"), [150, 0, 150, 255]))

    def unload(self, game):
        game.ui_manager.remove_text()
        game.ui_manager.remove_buttons()

    def input(self, game):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    match game.ui_manager.choice:
                        case 0: # CONTINUE
                            self.fading = -500
                            self.next_backend = GameState.PLAYING
                        case 1: # EXIT TO MAIN MENU
                            self.fading = -500
                            self.next_backend = GameState.MAIN_MENU
                        case 2: # EXIT TO DESKTOP
                            self.fading = -500
                            self.next_backend = GameState.QUITTING
                            return

        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        game.ui_manager.input(keys)

    def update(self, game):
        self.fade = max(0, min(255, int(self.fade + self.fading * game.delta_time)))
        if self.next_backend and (self.fade == 0 or self.fading == 0):
            if self.next_backend == GameState.QUITTING:
                game.running = False
                return
            game.set_backend(self.next_backend)

    def render(self, game):
        self.overlay.fill((0, 0, 0, 255 - self.fade))
        game.ui_manager.render()
        game.window_surface.blit(self.overlay, game.window_surface.get_rect())
        pygame.display.flip()