import pygame

from src.dialogue import Dialogue

class Text:
    def __init__(self, text: str, rect: pygame.Rect, font: pygame.font.Font):
        self.text: str = text
        self.rect: pygame.Rect = rect
        self.font: pygame.font.Font = font

class Button:
    def __init__(self, text: Text, select_pos: pygame.Vector2):
        self.text: Text = text
        self.select_pos: pygame.Vector2 = select_pos


class UIManager:
    def __init__(self, window_dims: pygame.Vector2, window_surface: pygame.Surface):
        self.window_dimensions: pygame.Vector2 = window_dims
        self.window_surface: pygame.Surface = window_surface

        self.dialogue: Dialogue | None = None

        self.text: list[Text] = []
        self.buttons: list[Button] = []
        self.choice: int = 0
        self.choice_move_block: bool = False

    def add_text(self, text: Text):
        self.text.append(text)

    def add_button(self, button: Button):
        self.buttons.append(button)

    def remove_text(self):
        self.text = []

    def remove_buttons(self):
        self.buttons = []

    def set_dialogue(self, dialogue: Dialogue):
        self.dialogue = dialogue

    def is_in_dialogue(self):
        return self.dialogue is not None and (self.dialogue.playing or self.dialogue.fade != 0)
    
    def input(self, keys: pygame.key.ScancodeWrapper):
        if self.is_in_dialogue(): self.dialogue.input(keys)

    def render_text(self, text: Text):
        rect: pygame.Rect = pygame.Rect(text.rect)
        y: int = rect.top
        line_spacing: int = -2

        font_height: int = text.font.size("Tg")[1]

        while text.text:
            i: int = 1

            if y + font_height > rect.bottom:
                break

            while text.font.size(text.text[:i])[0] < rect.width and i < len(text.text):
                i += 1

            if i < len(text.text):
                i = text.text.rfind(" ", 0, i) + 1

            img: pygame.Surface = text.font.render(text.text[:i], False, (255, 255, 255))
            self.window_surface.blit(img, (rect.left, y))
            y += font_height + line_spacing
            text.text = text.text[i:]

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

        for text in self.text:
            self.render_text(text)

        for button_i in range(len(self.buttons)):
            self.render_text(self.buttons[button_i].text)
            if self.choice == button_i:
                self.render_text(
                    Text("*", pygame.Rect(
                        self.buttons[button_i].text.rect.x + self.buttons[button_i].select_pos.x,
                        self.buttons[button_i].text.rect.y + self.buttons[button_i].select_pos.y,
                        self.buttons[button_i].text.rect.w,
                        self.buttons[button_i].text.rect.h,
                    ), self.buttons[button_i].text.font))