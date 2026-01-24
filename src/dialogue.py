import pygame


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

        self.line_index: list[int] = [0, len(self.lines)]
        self.char_index: list[int] = [0, len(self.lines[0])]

        self.char_duration: float = 0
        self.char_speeds: list[float] = char_speeds

    def line_finished(self) -> bool:
        return self.char_index[0] == self.char_index[1]

    def set_next_monologue(self, monologue):
        self.options = [("NEXT_MONOLOGUE_RESERVED", monologue)]

    def choose(self, choice: int):
        if not self.awaiting_choice: return None
        return self.options[choice][1]

    def reset(self):
        self.awaiting_choice = False
        self.spoken = ""
        self.line_index[0] = 0
        self.char_index[0] = 0
        self.char_index[1] = len(self.lines[0])

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

    def update(self, dt: float):
        self.char_duration += dt

        if self.char_duration >= self.char_speeds[self.line_index[0]] and self.char_index[0] != self.char_index[1]:
            self.char_duration = 0
            self.char_index[0] += 1
            self.spoken += self.lines[self.line_index[0]][self.char_index[0] - 1]

    def render(self, diag_surface: pygame.Surface):
        def render_text(text: str, rect: pygame.Rect):
            rect: pygame.Rect = pygame.Rect(rect)
            y: int = rect.top
            line_spacing: int = -2

            font_height: int = self.font.size("Tg")[1]

            while text:
                i: int = 1

                if y + font_height > rect.bottom:
                    break

                while self.font.size(text[:i])[0] < rect.width and i < len(text):
                    i += 1

                if i < len(text):
                    i = text.rfind(" ", 0, i) + 1

                img: pygame.Surface = self.font.render(text[:i], False, (255, 255, 255))
                diag_surface.blit(img, (rect.left, y))
                y += font_height + line_spacing
                text = text[i:]

        if self.speaker_image is not None:
            diag_surface.blit(self.speaker_image, pygame.Vector2(15, 15))
            render_text(
                self.speaker, pygame.Rect(
                    15 + self.speaker_image.get_width() + 30, 15,
                    diag_surface.get_width() - 90 - self.speaker_image.get_width(), 500)
            )
            render_text(
                self.spoken, pygame.Rect(
                    15 + self.speaker_image.get_width() + 60, 80,
                    diag_surface.get_width() - 90 - self.speaker_image.get_width(), 500)
            )
        else:
            render_text(self.speaker, pygame.Rect(35, 15, diag_surface.get_width() - 30, 500))
            render_text(self.spoken, pygame.Rect(65, 80, diag_surface.get_width() - 30, 500))


class Dialogue:
    def __init__(self, start_monologue: Monologue):
        self.start_monologue: Monologue = start_monologue
        self.current_monologue: Monologue = start_monologue

        self.playing: bool = False
        self.fade: int = 0
        self.fading: int = 0
        self.choice_index: int = 0

        self.advance_block: bool = True
        self.choice_move_block: bool = False

        self.draw_surface: pygame.Surface = pygame.Surface(
            (pygame.display.get_window_size()[0], pygame.display.get_window_size()[1] // 3))

    def start(self):
        self.playing = True
        self.fading = 1500

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
                return

            new_monologue: Monologue | None = self.current_monologue.skip()
            if new_monologue is not None:
                self.current_monologue = new_monologue
            else:
                self.playing = False
                self.fading = -1024
        else:
            self.advance_block = False

        moving: bool = False
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            moving = True
            if not self.choice_move_block:
                self.choice_index = min(len(self.current_monologue.options) - 1, self.choice_index + 1)
                self.choice_move_block = True
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            moving = True
            if not self.choice_move_block:
                self.choice_index = max(0, self.choice_index - 1)
                self.choice_move_block = True

        if not self.current_monologue.awaiting_choice: self.choice_index = 0

        if not moving:
            self.choice_move_block = False

    def update(self, dt: float):
        self.fade = max(0, min(255, int(self.fade + self.fading * dt)))
        if self.playing and self.fade == 255: self.current_monologue.update(dt)

    def render(self, sub_surface: pygame.Surface):
        if not self.playing and self.fade == 0: return
        self.draw_surface.fill((0, 0, 0))
        self.draw_surface.set_alpha(self.fade)
        self.current_monologue.render(self.draw_surface)
        sub_surface.blit(self.draw_surface, pygame.Vector2(0, 0))

        if self.playing and self.current_monologue.line_finished():
            tri_pos = pygame.Vector2(sub_surface.get_width() - 80, sub_surface.get_height() - 50)
            tri_coords: list[pygame.Vector2] = [
                pygame.Vector2(-1, -1),
                pygame.Vector2(0, 1),
                pygame.Vector2(1, -1)
            ]

            pygame.draw.polygon(sub_surface, (255, 255, 255), [c * 10 + tri_pos for c in tri_coords])
