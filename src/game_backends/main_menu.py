import pygame
import enum

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
        self.fade = 0
        self.fading = 500

        self.center_pos = game.window_surface.get_rect().center
        self.bottom_pos = game.window_surface.get_rect().midbottom
        self.top_pos = game.window_surface.get_rect().midtop

        self.switch_menu(game, Menu.MAIN)

    def unload(self, game) -> None:
        game.ui_manager.remove_text()
        game.ui_manager.remove_buttons()

    def switch_menu(self, game, new_menu: Menu) -> None:
        self.state = new_menu

        game.ui_manager.remove_text()
        game.ui_manager.remove_buttons()

        match new_menu:
            case Menu.MAIN:
                game.ui_manager.add_text(Text("Homegoing", [170, 20, 20, 255],
                    self.center_pos + pygame.Vector2(0, -230), True, game.asset_manager.get_font("snake192")))

                play_text: str = "Continue" if game.state_backends[GameState.PLAYING].is_setup else "Play"
                game.ui_manager.add_button(Button(Text(play_text, [255, 255, 255, 255],
                    self.center_pos + pygame.Vector2(0, -20), True, game.asset_manager.get_font("snake64")
                ), pygame.Vector2(-40, 0), game.asset_manager.get_font("snake40"), [150, 0, 150, 255]))

                game.ui_manager.add_button(Button(Text("How to play", [255, 255, 255, 255],
                    self.center_pos + pygame.Vector2(0, 60), True, game.asset_manager.get_font("snake64")
                ), pygame.Vector2(-40, 0), game.asset_manager.get_font("snake40"), [150, 0, 150, 255]))

                game.ui_manager.add_button(Button(Text("Credits", [255, 255, 255, 255],
                    self.center_pos + pygame.Vector2(0, 140), True, game.asset_manager.get_font("snake64")
                ), pygame.Vector2(-40, 0), game.asset_manager.get_font("snake40"), [150, 0, 150, 255]))

                game.ui_manager.add_button(Button(Text("Exit", [255, 255, 255, 255],
                    self.center_pos + pygame.Vector2(0, 220), True, game.asset_manager.get_font("snake64")
                ), pygame.Vector2(-40, 0), game.asset_manager.get_font("snake40"), [150, 0, 150, 255]))

            case Menu.HOW_TO_PLAY:
                game.ui_manager.add_text(
                    Text("How to play",
                         [170, 20, 20, 255],
                         self.center_pos + pygame.Vector2(0, -200), True,
                         game.asset_manager.get_font("snake64"))
                )
                game.ui_manager.add_text(
                    Text("Walk around and talk with W/A/S/D or the arrow keys",
                         [255, 255, 255, 255],
                         self.center_pos + pygame.Vector2(0, -60), True,
                         game.asset_manager.get_font("snake46"))
                )
                game.ui_manager.add_text(
                    Text("Interact with the environment with ENTER or SPACE",
                         [255, 255, 255, 255],
                         self.center_pos + pygame.Vector2(0, 0), True,
                         game.asset_manager.get_font("snake46"))
                )
                game.ui_manager.add_text(
                    Text("Talk to characters and complete objectives",
                         [255, 255, 255, 255],
                         self.center_pos + pygame.Vector2(0, 60), True,
                         game.asset_manager.get_font("snake46"))
                )

                game.ui_manager.add_button(Button(
                    Text("Understood", [255, 255, 255, 255],
                         self.center_pos + pygame.Vector2(0, 180), True,
                         game.asset_manager.get_font("snake64")
                    ), pygame.Vector2(-40, 0), game.asset_manager.get_font("snake40"), [150, 0, 150, 255]))

            case Menu.CREDITS:
                game.ui_manager.add_text(
                    Text("Credits",
                         [170, 20, 20, 255],
                         self.center_pos + pygame.Vector2(0, -300), True,
                         game.asset_manager.get_font("snake64"))
                ) 

                game.ui_manager.add_text(
                    Text("Mihir",
                         [255, 255, 255, 255],
                         self.center_pos + pygame.Vector2(-200, -160), False,
                         game.asset_manager.get_font("snake46"))
                )

                game.ui_manager.add_text(
                    Text("Programmer",
                         [255, 255, 255, 255],
                         self.center_pos + pygame.Vector2(200, -160), False,
                         game.asset_manager.get_font("snake46"))
                )

                game.ui_manager.add_text(
                    Text("Theodor",
                         [255, 255, 255, 255],
                         self.center_pos + pygame.Vector2(-200, -100), False,
                         game.asset_manager.get_font("snake46"))
                )

                game.ui_manager.add_text(
                    Text("Programmer",
                         [255, 255, 255, 255],
                         self.center_pos + pygame.Vector2(200, -100), False,
                         game.asset_manager.get_font("snake46"))
                )

                game.ui_manager.add_text(
                    Text("Abdulrahman",
                         [255, 255, 255, 255],
                         self.center_pos + pygame.Vector2(-200, -40), False,
                         game.asset_manager.get_font("snake46"))
                )

                game.ui_manager.add_text(
                    Text("Artist",
                         [255, 255, 255, 255],
                         self.center_pos + pygame.Vector2(200, -40), False,
                         game.asset_manager.get_font("snake46"))
                )

                game.ui_manager.add_text(
                    Text("Yazan",
                         [255, 255, 255, 255],
                         self.center_pos + pygame.Vector2(-200, 20), False,
                         game.asset_manager.get_font("snake46"))
                )

                game.ui_manager.add_text(
                    Text("Artist",
                         [255, 255, 255, 255],
                         self.center_pos + pygame.Vector2(200, 20), False,
                         game.asset_manager.get_font("snake46"))
                )

                game.ui_manager.add_text(
                    Text("Jonas",
                         [255, 255, 255, 255],
                         self.center_pos + pygame.Vector2(-200, 80), False,
                         game.asset_manager.get_font("snake46"))
                )

                game.ui_manager.add_text(
                    Text("Writer",
                         [255, 255, 255, 255],
                         self.center_pos + pygame.Vector2(200, 80), False,
                         game.asset_manager.get_font("snake46"))
                )

                game.ui_manager.add_button(Button(
                    Text("Back", [255, 255, 255, 255],
                         self.center_pos + pygame.Vector2(0, 200), True,
                         game.asset_manager.get_font("snake64")
                    ), pygame.Vector2(-40, 0), game.asset_manager.get_font("snake40"), [150, 0, 150, 255]))

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
        self.fade = max(0, min(255, int(self.fade + self.fading * game.delta_time)))
        if self.next_backend and (self.fade == 0 or self.fading == 0):
            if self.next_backend == GameState.QUITTING:
                game.running = False
                return
            game.set_backend(self.next_backend)

    def render(self, game) -> None:
        game.window_surface.fill((0, 0, 0))
        game.ui_manager.render()
        self.overlay.fill((0, 0, 0, 255 - self.fade))
        game.window_surface.blit(self.overlay, game.window_surface.get_rect())
        pygame.display.flip()
