import pygame

from src.ui_manager import UIManager, Text, Button

import src.config as cfg

SPEAKER_IMAGE_MARGIN_LEFT = 15
SPEAKER_IMAGE_MARGIN_TOP = 15

SPEAKER_TEXT_POS = pygame.Vector2(30, 15)
SPOKEN_TEXT_POS = pygame.Vector2(60, 80)
OPTIONS_START_RIGHT_PROPORTION = 1 / 5
OPTIONS_DISTANCE_BETWEEN = 15
OPTIONS_INDICATOR_OFFSET_X = 40

TRIANGLE_MARGIN_RIGHT = 80
TRIANGLE_MARGIN_BOTTOM = 50

FADE_SPEED = 1000

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
        if self.speaker_image is not None and self.speaker_image.get_width() == cfg.config.tile_size:
            size: int = cfg.config.dialogue_box_dims.y - SPEAKER_IMAGE_MARGIN_TOP * 2
            self.speaker_image = pygame.transform.scale(self.speaker_image, pygame.Vector2(size, size))

        self.awaiting_choice: bool = False
        self.options: list[tuple] = options or []
        self.has_options: bool = len(self.options) > 0
        self.next_monologue: Monologue | None = next_monologue

        self.is_final: bool = (not self.has_options) and self.next_monologue is None

        if not lines:
            raise ValueError("Monologue requires at least one line")

        self.spoken: str = ""
        self.line_index: list[int, int] = [0, len(self.lines)] # [ current, final ]
        self.char_index: list[int, int] = [0, len(self.lines[0])] # [ current, final ]

        if len(char_speeds) != len(lines):
            raise ValueError("char_speeds must have the same length as lines")

        self.char_duration: float = 0
        self.char_speeds: list[float] = char_speeds

        self.choice_fade: int = 0
        self.choice_fading: int = 0

        self.is_reset = True

    def line_finished(self) -> bool:
        return self.char_index[0] == self.char_index[1]

    def final_line(self) -> bool:
        return self.line_index[0] == self.line_index[1]

    def last_rendered_line(self) -> bool:
        return self.line_index[0] == self.line_index[1] - 1

    def set_next_monologue(self, monologue) -> None:
        self.next_monologue = monologue
        self.is_final = (not self.has_options) and self.next_monologue is None

    def add_option_monologue(self, option_title: str, monologue) -> None:
        self.options.append((option_title, monologue))
        self.is_final = (not self.has_options) and self.next_monologue is None

    def choose(self, choice: int):
        if not self.awaiting_choice: return None
        return self.options[choice][1]

    def reset(self) -> None:
        if self.is_reset: return

        self.awaiting_choice = False
        self.spoken = ""
        self.line_index[0] = 0
        self.char_index[0] = 0
        self.char_index[1] = len(self.lines[0])

        self.choice_fade: int = 0
        self.choice_fading: int = 0

        self.is_reset = True

        if self.next_monologue is not None: self.next_monologue.reset()
        for opt in self.options:
            opt[1].reset()

    def advance(self):
        if self.awaiting_choice: return

        if self.line_finished():
            self.line_index[0] += 1
            self.char_index[0] = 0

            if self.final_line():
                if self.is_final:
                    return None
                return self.next_monologue

            self.char_index[1] = len(self.lines[self.line_index[0]])
            return self
        self.spoken += self.lines[self.line_index[0]][self.char_index[0]:]
        self.char_index[0] = self.char_index[1]
        return self

    def update_fade(self, dt: float) -> None:
        self.choice_fading = FADE_SPEED if self.awaiting_choice else -FADE_SPEED
        self.choice_fade = pygame.math.clamp(self.choice_fade + self.choice_fading * dt, 0, 255)

    def update(self, dt: float) -> None:
        self.update_fade(dt)

        self.char_duration += dt

        if self.char_duration >= self.char_speeds[self.line_index[0]] and not self.line_finished():
            self.char_duration = 0
            self.char_index[0] += 1
            self.spoken += self.lines[self.line_index[0]][self.char_index[0] - 1]

        self.awaiting_choice = len(self.options) > 1 and self.line_finished() and self.last_rendered_line()

    def draw_text(self, surface: pygame.Surface, ui_manager: UIManager,
                  options_start: pygame.Vector2, start: pygame.Vector2, dims: pygame.Rect) -> None:

        ui_manager.draw_text(Text(
            self.speaker, [255, 255, 255, 255],
            start + SPEAKER_TEXT_POS, self.font,
            dimensions=pygame.Vector2(options_start.x - (start.x + SPEAKER_TEXT_POS.x),
                                      dims.height - SPEAKER_TEXT_POS.y)
        ), surface)

        ui_manager.draw_text(Text(
            self.spoken, [255, 255, 255, 255],
            start + SPOKEN_TEXT_POS, self.font,
            dimensions=pygame.Vector2(options_start.x - (start.x + SPOKEN_TEXT_POS.x),
                                      dims.height - SPOKEN_TEXT_POS.y)
        ), surface)

    def draw_options(self, surface: pygame.Surface, ui_manager: UIManager,
                     start: pygame.Vector2, dims: pygame.Rect) -> None:
        required_size: int = len(self.options) * (self.font.get_height() - OPTIONS_DISTANCE_BETWEEN)
        start.y = (dims.height - required_size) / 2

        ui_manager.set_num_buttons(len(self.options))

        for opt_i in range(len(self.options)):
            text: Text = Text(
                self.options[opt_i][0], [255, 255, 255, self.choice_fade],
                start, self.font,
                align_left=True
            )

            ui_manager.draw_button(Button(
                text, pygame.Vector2(-OPTIONS_INDICATOR_OFFSET_X, 0),
                self.font, [150, 0, 150, self.choice_fade]), opt_i, surface)
            start.y += text.rect.height - OPTIONS_DISTANCE_BETWEEN

    def render(self, draw_surface: pygame.Surface, dims: pygame.Rect, ui_manager: UIManager) -> None:
        options_start: pygame.Vector2 = pygame.Vector2(
            dims.width - pygame.display.get_window_size()[0] * OPTIONS_START_RIGHT_PROPORTION, 0
        )

        start: pygame.Vector2 = pygame.Vector2(0, 0)
        if self.speaker_image is not None:
            draw_surface.blit(self.speaker_image, pygame.Vector2(SPEAKER_IMAGE_MARGIN_LEFT, SPEAKER_IMAGE_MARGIN_TOP))

            start.x += SPEAKER_IMAGE_MARGIN_LEFT + self.speaker_image.get_width()

        self.draw_text(draw_surface, ui_manager, options_start, start, dims)

        if not self.awaiting_choice:
            ui_manager.set_num_buttons(0)
            return
        self.draw_options(draw_surface, ui_manager, options_start, dims)


class Dialogue:
    def __init__(self, start_monologue: Monologue):
        self.start_monologue: Monologue = start_monologue
        self.current_monologue: Monologue = start_monologue

        self.playing: bool = False
        self.fade: int = 0
        self.fading: int = 0
        self.choice_index: int = 0

        self.advance_block: bool = True

        self.draw_surface: pygame.Surface = pygame.Surface(cfg.config.dialogue_box_dims).convert()

        self.tri_coords: list[pygame.Vector2] = [
            pygame.Vector2(-1, -1),
            pygame.Vector2(0, 1),
            pygame.Vector2(1, -1)
        ]

    def start(self) -> None:
        self.playing = True
        self.fading = FADE_SPEED
        self.current_monologue.fading = FADE_SPEED
        self.current_monologue.is_reset = False

    def end(self) -> None:
        self.playing = False
        self.fading = -FADE_SPEED * 0.7
        self.current_monologue.fading = -FADE_SPEED * 0.7

    def reset(self) -> None:
        self.start_monologue.reset()
        self.current_monologue = self.start_monologue

    def choose_option(self) -> None:
        self.current_monologue = self.current_monologue.choose(self.choice_index)
        self.current_monologue.fade = 0
        self.current_monologue.fading = 0
        self.current_monologue.is_reset = False

    def load_monologue(self, monologue: Monologue) -> None:
        self.current_monologue = monologue
        self.current_monologue.fade = 0
        self.current_monologue.fading = 0
        self.current_monologue.is_reset = False

    def input(self, keys: pygame.key.ScancodeWrapper) -> None:
        if not self.playing: return
        if keys[pygame.K_RETURN] or keys[pygame.K_SPACE]:
            if self.advance_block: return
            self.advance_block = True

            if self.current_monologue.awaiting_choice:
                self.choose_option()
                return

            new_monologue: Monologue | None = self.current_monologue.advance()
            if new_monologue is not None:
                self.load_monologue(new_monologue)
            else:
                self.end()
        else:
            self.advance_block = False

    def update(self, ui_manager: UIManager, dt: float) -> None:
        self.fade = pygame.math.clamp(self.fade + self.fading * dt, 0, 255)

        if self.playing and self.fade == 255:
            self.current_monologue.update(dt)
        else:
            self.current_monologue.update_fade(dt)

        self.choice_index = ui_manager.choice

    def draw_triangle(self, surface: pygame.Surface, dims: pygame.Rect):
        tri_pos = pygame.Vector2(dims.x, dims.y) + pygame.Vector2(dims.width - TRIANGLE_MARGIN_RIGHT,
                                                                  dims.height - TRIANGLE_MARGIN_BOTTOM)

        pygame.draw.polygon(surface, cfg.config.dialogue_triangle_color, [c * 10 + tri_pos for c in self.tri_coords])

    def draw_dialogue_box(self):
        pygame.draw.rect(self.draw_surface, cfg.config.dialogue_box_outline_color, (
            0, 0, self.draw_surface.get_width(), self.draw_surface.get_height()
        ), width=cfg.config.dialogue_box_outline_thickness)

        pygame.draw.rect(self.draw_surface, (0, 0, 0), (
            cfg.config.dialogue_box_outline_thickness, cfg.config.dialogue_box_outline_thickness,
            self.draw_surface.get_width() - cfg.config.dialogue_box_outline_thickness * 2,
            self.draw_surface.get_height() - cfg.config.dialogue_box_outline_thickness
        ))

    def render(self, surface: pygame.Surface, dims: pygame.Rect, ui_manager: UIManager) -> None:
        if not self.playing and self.fade == 0: return

        self.draw_dialogue_box()
        self.current_monologue.render(self.draw_surface, dims, ui_manager)

        if self.fade < 255:
            self.draw_surface.set_alpha(self.fade)

        surface.blit(self.draw_surface, dims)

        if self.playing and self.current_monologue.line_finished() and not self.current_monologue.awaiting_choice:
            self.draw_triangle(surface, dims)