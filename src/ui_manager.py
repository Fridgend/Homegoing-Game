import pygame

from src.dialogue import Dialogue

class UIManager:
    def __init__(self, window_dims: pygame.Vector2, window_surface: pygame.Surface):
        self.window_dimensions: pygame.Vector2 = window_dims
        self.window_surface: pygame.Surface = window_surface

        self.dialogue: Dialogue = None

    def set_dialogue(self, dialogue: Dialogue):
        self.dialogue = dialogue

    def is_in_dialogue(self):
        return self.dialogue is not None and (self.dialogue.playing or self.dialogue.fade != 0)
    
    def input(self, keys: pygame.key.ScancodeWrapper):
        if self.is_in_dialogue(): self.dialogue.input(keys)

    def update(self, dt: float):
        if self.is_in_dialogue():
            self.dialogue.update(dt)
            if self.dialogue.fade == 0: self.dialogue.reset()

    def render(self):
        if self.dialogue is not None:
            surface: pygame.Surface = self.window_surface.subsurface(pygame.Rect(
                0, self.window_dimensions.y - self.window_dimensions.y // 3,
                self.window_dimensions.x, self.window_dimensions.y // 3)
            )
            self.dialogue.render(surface)