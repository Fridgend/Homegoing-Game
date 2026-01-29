import pygame

from src.game_backends.backend import Backend, GameState
from src.ui_manager import Text, Button

class PausedBackend(Backend):
    def __init__(self):
        super().__init__()

        self.center_pos: pygame.Vector2 = pygame.Vector2(0, 0)
        self.bottom_pos: pygame.Vector2 = pygame.Vector2(0, 0)
        self.top_pos: pygame.Vector2 = pygame.Vector2(0, 0)

    def init(self, game) -> None:
        self.next_backend = None
        self.fade = 255
        self.fading = 500

        self.overlay.fill((0, 0, 0))

        self.center_pos = game.window_surface.get_rect().center
        self.bottom_pos = game.window_surface.get_rect().midbottom
        self.top_pos = game.window_surface.get_rect().midtop 

        game.ui_manager.set_num_buttons(3)

    def unload(self, game) -> None:
        game.ui_manager.set_num_buttons(0)

    def input(self, game) -> None:
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

    def update(self, game) -> None:
        game.ui_manager.update(game.delta_time)
        self.fade = max(0, min(255, int(self.fade - self.fading * game.delta_time)))
        if self.next_backend and (self.fade == 255 or self.fading == 0):
            if self.next_backend == GameState.QUITTING:
                game.running = False
                return
            game.set_backend(self.next_backend)

    def render(self, game) -> None:
        game.window_surface.fill((0, 0, 0))
        self.overlay.set_alpha(self.fade)

        game.ui_manager.draw_button(Button(Text(
            "Continue", [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(0, -70), game.asset_manager.get_font("snake64"),
            align_center=True
        ), pygame.Vector2(-40, 0), game.asset_manager.get_font("snake40"), [150, 0, 150, 255]), 0)

        game.ui_manager.draw_button(Button(Text(
            "Exit to Main Menu", [255, 255, 255, 255],
            self.center_pos, game.asset_manager.get_font("snake64"),
            align_center=True
        ), pygame.Vector2(-40, 0), game.asset_manager.get_font("snake40"), [150, 0, 150, 255]), 1)

        game.ui_manager.draw_button(Button(Text(
            "Exit to Desktop", [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(0, 70), game.asset_manager.get_font("snake64"),
            align_center=True
        ), pygame.Vector2(-40, 0), game.asset_manager.get_font("snake40"), [150, 0, 150, 255]), 2)

        game.window_surface.blit(self.overlay, (0, 0))
        pygame.display.flip()
