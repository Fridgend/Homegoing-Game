import pygame

from src.game_backends.backend import Backend, GameState

class PlayingBackend(Backend):
    def __init__(self):
        super().__init__()
        self.is_setup: bool = False

    def init(self, game) -> None:
        if not self.is_setup:
            self.is_setup = True
            game.scene_manager.load_scene("test")

        game.scene_manager.scenes[game.scene_manager.current_scene].load()

        self.next_backend = None
        self.fade = 255
        self.fading = 500

        self.overlay.fill((0, 0, 0))

    def unload(self, game) -> None:
        game.scene_manager.scenes[game.scene_manager.current_scene].unload()

    def input(self, game) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
                return

            if self.fading != 0 and self.fade != 0 and self.fade != 255:
                continue

            if event.type == pygame.KEYDOWN and \
                    game.scene_manager.scenes[game.scene_manager.current_scene].dialogue is None:
                if event.key == pygame.K_ESCAPE:
                    self.fading = -500
                    self.next_backend = GameState.PAUSED

        if self.fading != 0 and self.fade != 0 and self.fade != 255: return

        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        game.scene_manager.input(game.ui_manager, keys)

    def update(self, game) -> None:
        game.camera.update(game.delta_time)

        game.scene_manager.update(game.camera, game.ui_manager, game.delta_time)
        self.fade = max(0, min(255, int(self.fade - self.fading * game.delta_time)))
        if self.next_backend and self.fade == 255:
            if self.next_backend == GameState.QUITTING:
                game.running = False
                return
            game.set_backend(self.next_backend)

    def render(self, game) -> None:
        game.scene_manager.render(game.window_surface, game.camera, game.ui_manager)

        if self.fade > 0:
            self.overlay.set_alpha(self.fade)
            game.window_surface.blit(self.overlay, (0, 0))

        pygame.display.flip()
