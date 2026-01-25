import pygame

from src.ui_manager import UIManager, Text, Button

class Monologue:
    def __init__(self,
                 speaker: str, lines: list[str], char_speeds: list[float],
                 font: pygame.font.Font,
                 next_monologue=None,
                 options: list[tuple] = None,
                 speaker_image: pygame.Surface | None = None):
        self.speaker: str = speaker
        self.lines: list[str] = lines
        self.font = font
        self.speaker_image: pygame.Surface | None = speaker_image
        if self.speaker_image is not None and self.speaker_image.get_width() == 32:
            size: int = pygame.display.get_window_size()[1] // 3
            self.speaker_image = pygame.transform.scale(self.speaker_image, pygame.Vector2(size - 30, size - 30))

        self.awaiting_choice: bool = False
        self.options: list[tuple] = options or []
        self.spoken: str = ""
        if next_monologue is not None:
            self.options.append(("NEXT_MONOLOGUE_RESERVED", next_monologue))

        if not lines:
            raise ValueError("Monologue requires at least one line")

        self.line_index: list[int] = [0, len(self.lines)]
        self.char_index: list[int] = [0, len(self.lines[0])]

        if len(char_speeds) != len(lines):
            raise ValueError("char_speeds must have the same length as lines")

        self.char_duration: float = 0
        self.char_speeds: list[float] = char_speeds

        self.fade: int = 0
        self.fading: int = 0
        self.choice_fade: int = 0
        self.choice_fading: int = 0

        self.is_reset = True

    def line_finished(self) -> bool:
        return self.char_index[0] == self.char_index[1]

    def set_next_monologue(self, monologue):
        self.options = [("NEXT_MONOLOGUE_RESERVED", monologue)]

    def add_option_monologue(self, option_title: str, monologue):
        self.options.append((option_title, monologue))

    def choose(self, choice: int):
        if not self.awaiting_choice: return None
        return self.options[choice][1]

    def reset(self):
        if self.is_reset: return

        self.awaiting_choice = False
        self.spoken = ""
        self.line_index[0] = 0
        self.char_index[0] = 0
        self.char_index[1] = len(self.lines[0])

        self.fade: int = 0
        self.fading: int = 0
        self.choice_fade: int = 0
        self.choice_fading: int = 0

        self.is_reset = True

        for opt in self.options:
            opt[1].reset()

    def skip(self):
        if self.awaiting_choice: return

        if self.char_index[0] == self.char_index[1]: # end of current line
            self.line_index[0] += 1
            self.char_index[0] = 0

            if self.line_index[0] == self.line_index[1]: # current line is final line of monologue
                if len(self.options) != 0:
                    return self.options[-1][1]
                return None

            self.char_index[1] = len(self.lines[self.line_index[0]])
            return self
        self.spoken += self.lines[self.line_index[0]][self.char_index[0]:]
        self.char_index[0] = self.char_index[1]
        return self

    def update_fade(self, dt: float):
        self.choice_fading = 1000 if self.awaiting_choice else -1000

        self.fade = max(0, min(255, int(self.fade + self.fading * dt)))
        self.choice_fade = max(0, min(255, int(self.choice_fade + self.choice_fading * dt)))

    def update(self, dt: float):
        self.update_fade(dt)

        self.char_duration += dt

        if self.char_duration >= self.char_speeds[self.line_index[0]] and self.char_index[0] != self.char_index[1]:
            self.char_duration = 0
            self.char_index[0] += 1
            self.spoken += self.lines[self.line_index[0]][self.char_index[0] - 1]

        self.awaiting_choice = len(self.options) > 1 and \
                               self.char_index[0] == self.char_index[1] and \
                               self.line_index[0] == self.line_index[1] - 1

    def render(self, draw_surface: pygame.Surface, draw_surface_pos: pygame.Vector2, ui_manager: UIManager):
        ui_manager.remove_text()
        ui_manager.remove_buttons(reset_choice=False)

        options_start: pygame.Vector2 = pygame.Vector2(draw_surface_pos.x + (draw_surface.get_width() - 350), 0)
        if self.speaker_image is not None:
            self.speaker_image.set_alpha(self.fade)
            draw_surface.blit(self.speaker_image, pygame.Vector2(15, 15))

            start: pygame.Vector2 = pygame.Vector2(15 + self.speaker_image.get_width(), draw_surface.get_rect().y) + \
                                    draw_surface_pos

            ui_manager.add_text(Text(
                self.speaker, [255, 255, 255, self.fade],
                start + pygame.Vector2(30, 15), False, self.font,
                dimensions=pygame.Vector2(options_start.x - (start.x + 30), draw_surface.get_height() - 15)
            ))

            ui_manager.add_text(Text(
                self.spoken, [255, 255, 255, self.fade],
                start + pygame.Vector2(60, 80), False, self.font,
                dimensions=pygame.Vector2(options_start.x - (start.x + 60), draw_surface.get_height() - 80)
            ))

        else:
            ui_manager.add_text(Text(
                self.speaker, [255, 255, 255, self.fade],
                pygame.Vector2(35, 15) + draw_surface_pos, False, self.font,
                dimensions=pygame.Vector2(options_start.x - 35, draw_surface.get_height() - 15)
            ))

            ui_manager.add_text(Text(
                self.spoken, [255, 255, 255, self.fade],
                pygame.Vector2(65, 80) + draw_surface_pos, False, self.font,
                dimensions=pygame.Vector2(options_start.x - 65, draw_surface.get_height() - 80)
            ))

        if not self.awaiting_choice: return

        required_size: int = len(self.options) * (self.font.get_height() - 15)
        options_start.y = draw_surface_pos.y + (draw_surface.get_height() - required_size) / 2

        for opt in self.options:
            if opt[0] == "NEXT_MONOLOGUE_RESERVED": continue
            text: Text = Text(opt[0], [255, 255, 255, self.choice_fade],
                options_start, False, self.font
            )

            ui_manager.add_button(Button(
                text, pygame.Vector2(-40, 0), self.font, [150, 0, 150, self.choice_fade]))
            options_start.y += text.rect.height - 15

class Dialogue:
    def __init__(self, start_monologue: Monologue):
        self.start_monologue: Monologue = start_monologue
        self.current_monologue: Monologue = start_monologue

        self.playing: bool = False
        self.fade: int = 0
        self.fading: int = 0
        self.choice_index: int = 0

        self.advance_block: bool = True

        self.draw_surface_pos: pygame.Vector2 = pygame.Vector2(
            pygame.display.get_window_size()[0] * 1 / 12, (2 * pygame.display.get_window_size()[1]) // 3)
        self.draw_surface: pygame.Surface = pygame.Surface(
            (pygame.display.get_window_size()[0] * 10 / 12, pygame.display.get_window_size()[1] // 3), pygame.SRCALPHA)

    def start(self):
        self.playing = True
        self.fading = 1500
        self.current_monologue.fading = 1500
        self.current_monologue.is_reset = False

    def reset(self):
        self.start_monologue.reset()
        self.current_monologue = self.start_monologue

    def input(self, keys: pygame.key.ScancodeWrapper):
        if not self.playing: return
        if keys[pygame.K_RETURN] or keys[pygame.K_SPACE]:
            if self.advance_block: return
            self.advance_block = True

            if self.current_monologue.awaiting_choice:
                self.current_monologue = self.current_monologue.choose(self.choice_index)
                self.current_monologue.fade = 255
                self.current_monologue.fading = 0
                self.current_monologue.is_reset = False
                return

            new_monologue: Monologue | None = self.current_monologue.skip()
            if new_monologue is not None:
                self.current_monologue = new_monologue
                self.current_monologue.fade = 255
                self.current_monologue.fading = 0
                self.current_monologue.is_reset = False
            else:
                self.playing = False
                self.fading = -1024
                self.current_monologue.fading = -1024
        else:
            self.advance_block = False

    def update(self, ui_manager: UIManager, dt: float):
        self.fade = max(0, min(255, int(self.fade + self.fading * dt)))

        if self.playing and self.fade == 255: self.current_monologue.update(dt)
        else: self.current_monologue.update_fade(dt)

        if self.fade == 0 and self.fading < 0: ui_manager.remove_text()

        self.choice_index = ui_manager.choice

    def render(self, sub_surface: pygame.Surface, ui_manager: UIManager):
        if not self.playing and self.fade == 0: return
        self.draw_surface.fill((255, 255, 255, self.fade))
        pygame.draw.rect(self.draw_surface, (0, 0, 0, self.fade), (
            3, 3, self.draw_surface.get_width() - 6, self.draw_surface.get_height() - 3))
        self.current_monologue.render(self.draw_surface, self.draw_surface_pos, ui_manager)
        sub_surface.blit(self.draw_surface, (0, 0))

        if self.playing and self.current_monologue.line_finished() and not self.current_monologue.awaiting_choice:
            tri_pos = pygame.Vector2(sub_surface.get_width() - 80, sub_surface.get_height() - 50)
            tri_coords: list[pygame.Vector2] = [
                pygame.Vector2(-1, -1),
                pygame.Vector2(0, 1),
                pygame.Vector2(1, -1)
            ]

            pygame.draw.polygon(sub_surface, (255, 255, 255), [c * 10 + tri_pos for c in tri_coords])
