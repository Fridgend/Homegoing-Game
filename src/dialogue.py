import pygame

from src.config import Config
from src.event import DispatchChain
from src.route_tracker import Conditions, Flags
from src.ui_manager import UIManager, Text, Button

SPEAKER_IMAGE_MARGIN_LEFT = 15
SPEAKER_IMAGE_MARGIN_TOP = 15

SPEAKER_TEXT_POS = pygame.Vector2(30, 15)
SPOKEN_TEXT_POS = pygame.Vector2(60, 80)
OPTIONS_START_RIGHT_PROPORTION = 1 / 4
OPTIONS_DISTANCE_BETWEEN = 15
OPTIONS_INDICATOR_OFFSET_X = 40

TRIANGLE_MARGIN_RIGHT = 80
TRIANGLE_MARGIN_BOTTOM = 50

FADE_SPEED = 1000

class MonologueLine:
    def __init__(self, text: str, speed: float):
        self.text: str = text
        self.speed: float = speed

class MonologueOption:
    def __init__(self, text: str, next_monologue: str, conditions: Conditions):
        self.text: str = text
        self.next_monologue: str = next_monologue
        self.conditions: Conditions = conditions


class Monologue:
    def __init__(self,
                 conditions: Conditions, alt_monologue: str,
                 speaker: str, lines: list[MonologueLine], font: pygame.font.Font,
                 next_monologue: str | None, set_route: list[tuple[str, Conditions]],
                 dispatch: DispatchChain, modify_flags: list[tuple[str, str]], options: list[MonologueOption],
                 speaker_image: pygame.Surface | None = None, speaking_sfx: pygame.mixer.Sound | None = None):
        self.conditions: Conditions = conditions
        self.alt_monologue: str = alt_monologue

        self.speaker: str = speaker
        self.lines: list[MonologueLine] = lines
        self.font = font

        self.next_monologue: str | None = next_monologue
        self.set_route: list[tuple[str, Conditions]] = set_route
        self.dispatch: DispatchChain = dispatch
        self.modify_flags: list[tuple[str, str]] = modify_flags
        self.options: list[MonologueOption] = options

        self.speaking_sfx: pygame.mixer.Sound | None = speaking_sfx
        self.speaker_image: pygame.Surface | None = speaker_image
        if self.speaker_image is not None:
            size: int = Config.DIALOGUE_BOX_DIMS.y - SPEAKER_IMAGE_MARGIN_TOP * 2
            self.speaker_image = pygame.transform.scale(self.speaker_image, pygame.Vector2(size, size))

        self.awaiting_choice: bool = False
        self.has_options: bool = len(self.options) > 0
        self.is_final: bool = (not self.has_options) and self.next_monologue is None

        if not lines:
            raise ValueError("Monologue requires at least one line")

        self.spoken: str = ""
        self.line_index: list[int] = [0, len(self.lines)] # [ current, final ]
        self.char_index: list[int] = [0, len(self.lines[0].text)] # [ current, final ]
        self.char_duration: float = 0

        self.choice_fade: int = 0
        self.choice_fading: int = 0

        self.is_reset = True

    def get_set_route(self) -> str | None:
        for (route, conditions) in self.set_route:
            if conditions.satisfied():
                return route
        return None

    def line_finished(self) -> bool:
        return self.char_index[0] == self.char_index[1]

    def final_line(self) -> bool:
        return self.line_index[0] == self.line_index[1]

    def last_rendered_line(self) -> bool:
        return self.line_index[0] == self.line_index[1] - 1

    def set_next_monologue(self, monologue: str) -> None:
        self.next_monologue = monologue
        self.is_final = (not self.has_options) and self.next_monologue is None

    def add_option(self, option: MonologueOption) -> None:
        self.options.append(option)
        self.has_options = len(self.options) > 0
        self.is_final = (not self.has_options) and self.next_monologue is None

    def choose(self, choice: int) -> str | None:
        if not self.awaiting_choice: return None
        return self.options[choice].next_monologue

    def reset(self) -> None:
        if self.is_reset: return

        self.awaiting_choice = False
        self.spoken = ""
        self.line_index[0] = 0
        self.char_index[0] = 0
        self.char_index[1] = len(self.lines[0].text)

        self.choice_fade: int = 0
        self.choice_fading: int = 0

        self.is_reset = True

    def advance(self) -> str | None:
        if self.awaiting_choice: return None

        if self.line_finished():
            self.line_index[0] += 1
            self.char_index[0] = 0

            if self.final_line():
                if self.is_final:
                    return None
                return self.next_monologue

            self.char_index[1] = len(self.lines[self.line_index[0]].text)
            return ""
        self.spoken += self.lines[self.line_index[0]].text[self.char_index[0]:]
        self.char_index[0] = self.char_index[1]
        return ""

    def update_fade(self, dt: float) -> None:
        self.choice_fading = FADE_SPEED if self.awaiting_choice else -FADE_SPEED
        self.choice_fade = pygame.math.clamp(self.choice_fade + self.choice_fading * dt, 0, 255)

    def update(self, dt: float) -> None:
        self.update_fade(dt)

        self.char_duration += dt

        if self.char_duration >= self.lines[self.line_index[0]].speed and not self.line_finished():
            self.char_duration = 0
            self.spoken += self.lines[self.line_index[0]].text[self.char_index[0]]
            self.char_index[0] += 1
            if self.speaking_sfx is not None:
                self.speaking_sfx.play(maxtime=int(self.lines[self.line_index[0]].speed * 2000))

        self.awaiting_choice = len(self.options) > 0 and self.line_finished() and self.last_rendered_line()

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
                self.options[opt_i].text, [255, 255, 255, self.choice_fade],
                start, self.font,
                align_left=True
            )

            ui_manager.draw_button(Button(
                text, pygame.Vector2(-OPTIONS_INDICATOR_OFFSET_X, 0),
                self.font, [150, 0, 150, self.choice_fade]), opt_i, surface)
            start.y += text.rect.height - OPTIONS_DISTANCE_BETWEEN

    def render(self, draw_surface: pygame.Surface, dims: pygame.Rect, ui_manager: UIManager) -> None:
        options_start: pygame.Vector2 = pygame.Vector2(
            dims.width - dims.width * OPTIONS_START_RIGHT_PROPORTION, 0
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
    def __init__(self, conditions: Conditions, start_monologues: list[tuple[str, Conditions]],
                 monologues: dict[str, Monologue], entity_id: str):
        self.conditions: Conditions = conditions
        self.start_monologues: list[tuple[str, Conditions]] = start_monologues
        self.monologues: dict[str, Monologue] = monologues

        self.entity_id: str = entity_id

        self.current_monologue: str = ""

        self.playing: bool = False
        self.fade: int = 0
        self.fading: int = 0
        self.choice_index: int = 0

        self.advance_block: bool = True

        self.draw_surface: pygame.Surface = pygame.Surface(Config.DIALOGUE_BOX_DIMS).convert()

        self.tri_coords: list[pygame.Vector2] = [
            pygame.Vector2(-1, -1),
            pygame.Vector2(0, 1),
            pygame.Vector2(1, -1)
        ]

    def start(self, scene) -> bool:
        self.playing = True
        self.fading = FADE_SPEED
        for (monologue_id, conditions) in self.start_monologues:
            if conditions.satisfied():
                self.current_monologue = monologue_id
                break
        if self.current_monologue == "":
            self.playing = True
            self.fading = 0
            return True

        while not self.monologues.get(self.current_monologue).conditions.satisfied():
            self.current_monologue = self.monologues.get(self.current_monologue).alt_monologue
        if self.current_monologue == "":
            self.playing = True
            self.fading = 0
            return True

        self.handle_new_monologue(scene)
        self.monologues.get(self.current_monologue).fading = FADE_SPEED
        self.monologues.get(self.current_monologue).is_reset = False
        return False

    def end(self) -> None:
        self.playing = False
        self.fading = -FADE_SPEED * 0.7
        self.monologues.get(self.current_monologue).fading = -FADE_SPEED * 0.7

    def reset(self) -> None:
        for _, monologue in self.monologues.items():
            monologue.reset()
        for (monologue_id, conditions) in self.start_monologues:
            if conditions.satisfied():
                self.current_monologue = monologue_id
                break

    def handle_new_monologue(self, scene):
        route: str | None = self.monologues.get(self.current_monologue).get_set_route()

        if route is not None:
            scene.entities_dict[self.entity_id].set_route(route)

        for (method, flag) in self.monologues.get(self.current_monologue).modify_flags:
            Flags.modify(flag=flag, how=method)

        scene.add_dispatch_chain(self.monologues.get(self.current_monologue).dispatch)

    def choose_option(self, scene) -> None:
        self.current_monologue = self.monologues.get(self.current_monologue).choose(self.choice_index)
        while not self.monologues.get(self.current_monologue).conditions.satisfied():
            self.current_monologue = self.monologues.get(self.current_monologue).alt_monologue
        self.monologues.get(self.current_monologue).is_reset = False
        self.handle_new_monologue(scene)

    def load_monologue(self, monologue_id: str, scene) -> None:
        self.current_monologue = monologue_id
        while not self.monologues.get(self.current_monologue).conditions.satisfied():
            self.current_monologue = self.monologues.get(self.current_monologue).alt_monologue
        self.monologues.get(self.current_monologue).is_reset = False
        self.handle_new_monologue(scene)

    def input(self, scene, keys: pygame.key.ScancodeWrapper) -> None:
        if not self.playing: return
        if keys[pygame.K_RETURN] or keys[pygame.K_SPACE]:
            if self.advance_block: return
            self.advance_block = True

            if self.monologues.get(self.current_monologue).awaiting_choice:
                self.choose_option(scene)
                return

            new_monologue: str | None = self.monologues.get(self.current_monologue).advance()
            if new_monologue == "":
                return

            if new_monologue is not None:
                self.load_monologue(new_monologue, scene)
            else:
                self.end()
        else:
            self.advance_block = False

    def update(self, ui_manager: UIManager, scene, dt: float) -> None:
        self.fade = pygame.math.clamp(self.fade + self.fading * dt, 0, 255)

        if self.playing and self.fade == 255:
            self.monologues.get(self.current_monologue).update(dt)
        else:
            self.monologues.get(self.current_monologue).update_fade(dt)

        self.choice_index = ui_manager.choice

    def draw_triangle(self, surface: pygame.Surface, dims: pygame.Rect):
        tri_pos = pygame.Vector2(dims.x, dims.y) + pygame.Vector2(dims.width - TRIANGLE_MARGIN_RIGHT,
                                                                  dims.height - TRIANGLE_MARGIN_BOTTOM)

        pygame.draw.polygon(surface, Config.DIALOGUE_TRIANGLE_COLOR, [c * 10 + tri_pos for c in self.tri_coords])

    def draw_dialogue_box(self):
        pygame.draw.rect(self.draw_surface, Config.DIALOGUE_BOX_OUTLINE_COLOR, (
            0, 0, Config.DIALOGUE_BOX_DIMS.x, Config.DIALOGUE_BOX_DIMS.y
        ), width=Config.DIALOGUE_BOX_OUTLINE_THICKNESS)

        pygame.draw.rect(self.draw_surface, Config.DIALOGUE_BOX_BACKGROUND_COLOR, (
            Config.DIALOGUE_BOX_OUTLINE_THICKNESS, Config.DIALOGUE_BOX_OUTLINE_THICKNESS,
            Config.DIALOGUE_BOX_DIMS.x - Config.DIALOGUE_BOX_OUTLINE_THICKNESS * 2,
            Config.DIALOGUE_BOX_DIMS.y - Config.DIALOGUE_BOX_OUTLINE_THICKNESS
        ))

    def render(self, surface: pygame.Surface, dims: pygame.Rect, ui_manager: UIManager) -> None:
        if not self.playing and self.fade == 0: return

        self.draw_dialogue_box()
        self.monologues.get(self.current_monologue).render(self.draw_surface, dims, ui_manager)

        if self.fade < 255:
            self.draw_surface.set_alpha(self.fade)

        surface.blit(self.draw_surface, dims)

        if self.playing and self.monologues.get(self.current_monologue).line_finished() and \
                not self.monologues.get(self.current_monologue).awaiting_choice:
            self.draw_triangle(surface, dims)
