import pygame

from src.game_backends.backend import Backend, GameState

from src.scenes import test_scene

class PlayingBackend(Backend):
    def __init__(self):
        super().__init__()
        pass

    def init(self, game):
        game.scene_manager.add_scene("test", test_scene.TestScene())
        game.scene_manager.load_scene("test", game.asset_manager)

        self.next_backend = None
        self.fade = 0
        self.fading = 500

    def input(self, game):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.fading = -500
                    self.next_backend = GameState.MAIN_MENU

        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        game.scene_manager.input(game.ui_manager, keys)

    def update(self, game):
        game.scene_manager.update(game.camera, game.ui_manager, game.delta_time)
        self.fade = max(0, min(255, int(self.fade + self.fading * game.delta_time)))
        if self.next_backend and self.fade == 0: game.set_backend(self.next_backend)

    def render(self, game):
        game.scene_manager.render(game.window_surface, game.camera)
        game.ui_manager.render()
        if self.fade != 0: self.overlay.fill((0, 0, 0, 255 - self.fade))
        game.window_surface.blit(self.overlay, game.window_surface.get_rect())
        pygame.display.flip()