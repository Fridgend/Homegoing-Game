import pygame

import src.config as cfg

class Text:
    def __init__(self, text: str, color: list, pos: pygame.Vector2, font: pygame.font.Font,
                 align_left: bool = False, align_center: bool = False, align_right: bool = False,
                 dimensions: pygame.Vector2 = pygame.Vector2(0, 0)):
        self.text: str = text
        self.font: pygame.font.Font = font
        self.pos: pygame.Vector2 = pos
        self.color: list = color

        if align_left:
            self.rect = self.font.render(text, True, color).get_rect()
            self.rect.x = self.pos.x
            self.rect.y = self.pos.y
        elif align_center:
            self.rect = self.font.render(text, True, color).get_rect(center=pos)
        elif align_right:
            self.rect = self.font.render(text, True, color).get_rect(topright=pos)
        else:
            self.rect = pygame.Rect(self.pos.x, self.pos.y, dimensions.x, dimensions.y)

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

        self.num_buttons: int = 0
        self.choice: int = 0
        self.choice_move_block: bool = False

    def set_dialogue(self, dialogue) -> None:
        self.dialogue = dialogue

    def is_in_dialogue(self) -> bool:
        return self.dialogue is not None and (self.dialogue.playing or self.dialogue.fade != 0)

    def set_num_buttons(self, buttons: int) -> None:
        if buttons != self.num_buttons: self.choice = 0
        self.num_buttons = buttons

    def draw_text(self, text: Text, surface: pygame.Surface = None) -> None:
        self._render_text(text)

    def draw_button(self, button: Button, button_index: int, surface: pygame.Surface = None) -> None:
        self._render_text(button.text)
        if self.choice == button_index:
            self._render_text(
                Text("*", button.select_color, button.text.rect.midleft + button.select_pos,
                     button.select_font, align_center=True)
            )
    
    def input(self, keys: pygame.key.ScancodeWrapper) -> None:
        if self.is_in_dialogue(): self.dialogue.input(keys)

        moving: bool = False

        if self.num_buttons > 0:
            if keys[pygame.K_DOWN] or keys[pygame.K_s] or keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                moving = True
                if not self.choice_move_block:
                    self.choice += 1
                    self.choice_move_block = True
            elif keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_LEFT] or keys[pygame.K_a]:
                moving = True
                if not self.choice_move_block:
                    self.choice -= 1
                    self.choice_move_block = True
        else: self.choice = 0

        if not moving:
            self.choice_move_block = False

    def _render_text(self, text: Text) -> None:
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

                img: pygame.Surface = text.font.render(line[:i], False, text.color[:3]).convert()
                img.set_alpha(text.color[3])
                blits.append((img, (rect.left, y)))
                y += font_height + line_spacing
                line = line[i:]

        self.window_surface.blits(blits)

    def update(self, dt: float) -> None:
        if self.is_in_dialogue():
            self.dialogue.update(self, dt)
            if self.dialogue.fade == 0: self.dialogue.reset()

        if self.num_buttons > 0:
            self.choice = pygame.math.clamp(self.choice, 0, self.num_buttons - 1)

    def render(self) -> None:
        if self.dialogue is not None:
            surface: pygame.Surface = self.window_surface.subsurface(pygame.Rect(
                cfg.config.window_dims.x * 1 / 12, cfg.config.window_dims.y - cfg.config.window_dims.y // 3,
                cfg.config.window_dims.x * 10 / 12, cfg.config.window_dims.y // 3)
            )
            self.dialogue.render(surface, self)
