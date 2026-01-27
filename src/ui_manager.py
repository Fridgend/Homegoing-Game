import pygame

import src.config as cfg

class Text:
    def __init__(self, text: str, color: list, pos: pygame.Vector2, centered: bool, font: pygame.font.Font,
                 dimensions: pygame.Vector2 | None = None):
        self.text: str = text
        self.font: pygame.font.Font = font
        self.centered: bool = centered
        self.pos: pygame.Vector2 = pos
        self.color: list = color

        if centered:
            self.rect = self.font.render(text, True, color).get_rect(center=pos)
        else:
            if dimensions is not None:
                self.rect = pygame.Rect(self.pos, dimensions)
            else:
                self.rect = self.font.render(text, True, color).get_rect()
                self.rect.x = self.pos.x
                self.rect.y = self.pos.y

class Button:
    def __init__(self, text: Text, select_pos: pygame.Vector2,
                 select_font: pygame.font.Font, select_color: list):
        self.text: Text = text
        self.select_pos: pygame.Vector2 = select_pos
        self.select_font: pygame.font.Font = select_font
        self.select_color: list = select_color


class UIManager:
    def __init__(self, window_surface: pygame.Surface):
        self.window_surface: pygame.Surface = window_surface

        self.dialogue = None
        self.fade: int = 255

        self.text: list[Text] = []
        self.buttons: list[Button] = []
        self.choice: int = 0
        self.choice_move_block: bool = False

    def set_text_fade(self, text_i: int, fade: int) -> None:
        self.text[text_i].color[3] = fade

    def set_button_fade(self, button_i: int, fade: int) -> None:
        self.buttons[button_i].text.color[3] = fade
        self.buttons[button_i].select_color[3] = fade

    def set_text_fades(self, fade: int) -> None:
        for i in range(len(self.text)):
            self.set_text_fade(i, fade)

    def set_button_fades(self, fade: int) -> None:
        for i in range(len(self.buttons)):
            self.set_button_fade(i, fade)

    def add_text(self, text: Text) -> None:
        self.text.append(text)

    def add_button(self, button: Button) -> None:
        self.buttons.append(button)

    def remove_text(self) -> None:
        self.text = []

    def remove_buttons(self, reset_choice: bool = True) -> None:
        self.buttons = []
        self.choice = 0 if reset_choice else self.choice

    def set_dialogue(self, dialogue) -> None:
        self.dialogue = dialogue

    def is_in_dialogue(self) -> bool:
        return self.dialogue is not None and (self.dialogue.playing or self.dialogue.fade != 0)
    
    def input(self, keys: pygame.key.ScancodeWrapper) -> None:
        if self.is_in_dialogue(): self.dialogue.input(keys)

        moving: bool = False
        if len(self.buttons) > 0 and (
                keys[pygame.K_DOWN] or keys[pygame.K_s] or keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            moving = True
            if not self.choice_move_block:
                self.choice = min(len(self.buttons) - 1, self.choice + 1)
                self.choice_move_block = True
        if len(self.buttons) > 0 and (
                keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_LEFT] or keys[pygame.K_a]):
            moving = True
            if not self.choice_move_block:
                self.choice = max(0, self.choice - 1)
                self.choice_move_block = True

        if not len(self.buttons) > 0: self.choice = 0

        if not moving:
            self.choice_move_block = False

    def render_text(self, text: Text) -> None:
        rect: pygame.Rect = pygame.Rect(text.rect)
        y: int = rect.top
        line_spacing: int = -2
        font_height: int = text.font.size("Tg")[1]

        write: str = text.text
        lines: list[str] = write.split("\n")

        blits: list = []
        for line in lines:
            while line:
                i: int = 1

                while text.font.size(line[:i])[0] < rect.width and i < len(line):
                    i += 1

                if i < len(line):
                    split_idx: int = line.rfind(" ", 0, i)
                    i = split_idx + 1 if split_idx != -1 else i

                img: pygame.Surface = text.font.render(line[:i], False, text.color[:3])
                img.set_alpha(text.color[3])
                blits.append((img, (rect.left, y)))
                y += font_height + line_spacing
                line = line[i:]

        self.window_surface.blits(blits)

    def update(self, dt: float) -> None:
        if self.is_in_dialogue():
            self.dialogue.update(self, dt)
            if self.dialogue.fade == 0: self.dialogue.reset()

    def render(self) -> None:
        if self.dialogue is not None:
            surface: pygame.Surface = self.window_surface.subsurface(pygame.Rect(
                cfg.config.window_dims.x * 1 / 12, cfg.config.window_dims.y - cfg.config.window_dims.y // 3,
                cfg.config.window_dims.x * 10 / 12, cfg.config.window_dims.y // 3)
            )
            self.dialogue.render(surface, self)

        for text in self.text:
            self.render_text(text)

        for button_i in range(len(self.buttons)):
            self.render_text(self.buttons[button_i].text)
            if self.choice == button_i:
                self.render_text(
                    Text("*", self.buttons[button_i].select_color,
                         self.buttons[button_i].text.rect.midleft + self.buttons[button_i].select_pos, True,
                         self.buttons[button_i].select_font)
                )