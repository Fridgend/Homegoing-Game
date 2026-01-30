import pygame

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


def _render_text(text: Text, surface: pygame.Surface) -> None:
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
            if text.color[3] < 255: img.set_alpha(text.color[3])
            blits.append((img, (rect.left, y)))
            y += font_height + line_spacing
            line = line[i:]

    surface.blits(blits)


class UIManager:
    def __init__(self, window_surface: pygame.Surface):
        self.window_surface: pygame.Surface = window_surface

        self.num_buttons: int = 0
        self.choice: int = 0
        self.choice_move_block: bool = False

    def set_num_buttons(self, buttons: int) -> None:
        if buttons != self.num_buttons: self.choice = 0
        self.num_buttons = buttons

    def draw_text(self, text: Text, surface: pygame.Surface = None) -> None:
        _render_text(text, surface if surface is not None else self.window_surface)

    def draw_button(self, button: Button, button_index: int, surface: pygame.Surface = None) -> None:
        _render_text(button.text, surface if surface is not None else self.window_surface)
        if self.choice == button_index:
            _render_text(Text(
                "*", button.select_color,
                button.text.rect.midleft + button.select_pos,
                button.select_font, align_center=True
            ), surface if surface is not None else self.window_surface)
    
    def input(self, keys: pygame.key.ScancodeWrapper) -> None:
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

    def update(self) -> None:
        if self.num_buttons > 0:
            self.choice = pygame.math.clamp(self.choice, 0, self.num_buttons - 1)