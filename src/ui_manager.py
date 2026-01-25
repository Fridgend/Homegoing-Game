import pygame

class Text:
    def __init__(self, text: str, color: pygame.Vector3, pos: pygame.Vector2, centered: bool, font: pygame.font.Font,
                 dimensions: pygame.Vector2 | None = None):
        self.text: str = text
        self.font: pygame.font.Font = font
        self.centered: bool = centered
        self.pos: pygame.Vector2 = pos
        self.color: pygame.Vector3 = color

        if centered:
            self.rect = self.font.render(text, True, color).get_rect(center=pos)
        else:
            self.rect = pygame.Rect(self.pos, dimensions)

class Button:
    def __init__(self, text: Text, select_pos: pygame.Vector2,
                 select_font: pygame.font.Font, select_color: pygame.Vector3):
        self.text: Text = text
        self.select_pos: pygame.Vector2 = select_pos
        self.select_font: pygame.font.Font = select_font
        self.select_color: pygame.Vector3 = select_color


class UIManager:
    def __init__(self, window_dims: pygame.Vector2, window_surface: pygame.Surface):
        self.window_dimensions: pygame.Vector2 = window_dims
        self.window_surface: pygame.Surface = window_surface

        self.dialogue = None

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

    def remove_buttons(self, reset_choice: bool = True):
        self.buttons = []
        self.choice = 0 if reset_choice else self.choice

    def set_dialogue(self, dialogue):
        self.dialogue = dialogue

    def is_in_dialogue(self):
        return self.dialogue is not None and (self.dialogue.playing or self.dialogue.fade != 0)
    
    def input(self, keys: pygame.key.ScancodeWrapper):
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

    def render_text(self, text: Text):
        rect: pygame.Rect = pygame.Rect(text.rect)
        y: int = rect.top
        line_spacing: int = -2

        font_height: int = text.font.size("Tg")[1]

        write = text.text

        while write:
            i: int = 1

            if y + font_height > rect.bottom:
                break

            while text.font.size(write[:i])[0] < rect.width and i < len(write):
                i += 1

            if i < len(write):
                i = write.rfind(" ", 0, i) + 1

            img: pygame.Surface = text.font.render(write[:i], False, text.color)
            self.window_surface.blit(img, (rect.left, y))
            y += font_height + line_spacing
            write = write[i:]

    def update(self, dt: float):
        if self.is_in_dialogue():
            self.dialogue.update(self, dt)
            if self.dialogue.fade == 0: self.dialogue.reset()

    def render(self):
        if self.dialogue is not None:
            surface: pygame.Surface = self.window_surface.subsurface(pygame.Rect(
                0, self.window_dimensions.y - self.window_dimensions.y // 3,
                self.window_dimensions.x, self.window_dimensions.y // 3)
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