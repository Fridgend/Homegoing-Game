import pygame
import enum

from src.asset_manager import AssetManager
from src.game_backends.backend import Backend, GameState
from src.ui_manager import Text, Button

class Menu(enum.Enum):
    MAIN = 0
    HOW_TO_PLAY = 1
    CREDITS = 2

class MainMenuBackend(Backend):
    def __init__(self):
        super().__init__()

        self.state: Menu = Menu.MAIN

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

        self.switch_menu(game, Menu.MAIN)

    def unload(self, game) -> None:
        game.ui_manager.set_num_buttons(0)

    def switch_menu(self, game, new_menu: Menu) -> None:
        self.state = new_menu

        match new_menu:
            case Menu.MAIN:
                game.ui_manager.set_num_buttons(4)

            case Menu.HOW_TO_PLAY:
                game.ui_manager.set_num_buttons(1)

            case Menu.CREDITS:
                game.ui_manager.set_num_buttons(1)

    def input(self, game) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    match self.state:
                        case Menu.MAIN:
                            match game.ui_manager.choice:
                                case 0: # PLAY
                                    self.fading = -500
                                    self.next_backend = GameState.PLAYING
                                    game.ui_manager.set_num_buttons(0)
                                case 1: # HOW TO PLAY
                                    self.switch_menu(game, Menu.HOW_TO_PLAY)
                                case 2: # CREDITS
                                    self.switch_menu(game, Menu.CREDITS)
                                case 3: # EXIT
                                    self.fading = -500
                                    self.next_backend = GameState.QUITTING
                                    return
                        case Menu.HOW_TO_PLAY:
                            self.switch_menu(game, Menu.MAIN)
                        case Menu.CREDITS:
                            self.switch_menu(game, Menu.MAIN)

        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        game.ui_manager.input(keys)

    def update(self, game) -> None:
        game.ui_manager.update()
        self.fade = max(0, min(255, int(self.fade - self.fading * game.delta_time)))
        if self.next_backend and (self.fade == 255 or self.fading == 0):
            if self.next_backend == GameState.QUITTING:
                game.running = False
                return
            game.set_backend(self.next_backend)

    def render_main_menu(self, game) -> None:
        game.ui_manager.draw_text(Text(
            "Homegoing", [170, 20, 20, 255],
            self.center_pos + pygame.Vector2(0, -230), AssetManager.get_font("snake192"),
            align_center=True
        ))

        play_text: str = "Continue" if game.state_backends[GameState.PLAYING].is_setup else "Play"
        game.ui_manager.draw_button(Button(Text(
            play_text, [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(0, -20), AssetManager.get_font("snake64"),
            align_center=True
        ), pygame.Vector2(-40, 0), AssetManager.get_font("snake40"), [150, 0, 150, 255]), 0)

        game.ui_manager.draw_button(Button(Text(
            "How to Play", [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(0, 60), AssetManager.get_font("snake64"),
            align_center=True
        ), pygame.Vector2(-40, 0), AssetManager.get_font("snake40"), [150, 0, 150, 255]), 1)

        game.ui_manager.draw_button(Button(Text(
            "Credits", [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(0, 140), AssetManager.get_font("snake64"),
            align_center=True
        ), pygame.Vector2(-40, 0), AssetManager.get_font("snake40"), [150, 0, 150, 255]), 2)

        game.ui_manager.draw_button(Button(Text(
            "Exit", [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(0, 220), AssetManager.get_font("snake64"),
            align_center=True
        ), pygame.Vector2(-40, 0), AssetManager.get_font("snake40"), [150, 0, 150, 255]), 3)

    def render_how_to_play(self, game) -> None:
        game.ui_manager.draw_text(Text(
            "How to Play", [170, 20, 20, 255],
            self.center_pos + pygame.Vector2(0, -200), AssetManager.get_font("snake64"),
            align_center=True
        ))

        game.ui_manager.draw_text(Text(
            "Walk around and talk with WASD or the arrow keys", [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(0, -60), AssetManager.get_font("snake46"),
            align_center=True
        ))

        game.ui_manager.draw_text(Text(
            "Interact with the environment with ENTER or SPACE", [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(0, 0), AssetManager.get_font("snake46"),
            align_center=True
        ))

        game.ui_manager.draw_text(Text(
            "Talk to characters and complete objectives", [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(0, 60), AssetManager.get_font("snake46"),
            align_center=True
        ))

        game.ui_manager.draw_button(Button(Text(
            "Understood", [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(0, 180), AssetManager.get_font("snake64"),
            align_center=True
        ), pygame.Vector2(-40, 0), AssetManager.get_font("snake40"), [150, 0, 150, 255]), 0)

    def render_credit(self, game, name: str, role: str, y: int):
        game.ui_manager.draw_text(Text(
            name, [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(-200, y), AssetManager.get_font("snake46"),
            align_left=True
        ))

        game.ui_manager.draw_text(Text(
            role, [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(200, y), AssetManager.get_font("snake46"),
            align_right=True
        ))

    def render_credits(self, game) -> None:
        game.ui_manager.draw_text(Text(
            "Credits", [170, 20, 20, 255],
            self.center_pos + pygame.Vector2(0, -250), AssetManager.get_font("snake64"),
            align_center=True
        ))

        game.ui_manager.draw_text(Text(
            "Based on the novel by Yaa Gyasi", [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(0, -175), AssetManager.get_font("snake40"),
            align_center=True
        ))

        self.render_credit(game, "Mihir", "Programmer", -110)
        self.render_credit(game, "Theodor", "Programmer", -50)
        self.render_credit(game, "Abdulrahman", "Artist", 10)
        self.render_credit(game, "Yazan", "Artist", 70)
        self.render_credit(game, "Jonas", "Writer", 130)

        game.ui_manager.draw_button(Button(Text(
            "Back", [255, 255, 255, 255],
            self.center_pos + pygame.Vector2(0, 250), AssetManager.get_font("snake64"),
            align_center=True
        ), pygame.Vector2(-40, 0), AssetManager.get_font("snake40"), [150, 0, 150, 255]), 0)

    def render(self, game) -> None:
        game.window_surface.fill((0, 0, 0))

        match self.state:
            case Menu.MAIN:
                self.render_main_menu(game)
            case Menu.HOW_TO_PLAY:
                self.render_how_to_play(game)
            case Menu.CREDITS:
                self.render_credits(game)

        if self.fade > 0:
            self.overlay.set_alpha(self.fade)
            game.window_surface.blit(self.overlay, (0, 0))

        pygame.display.flip()