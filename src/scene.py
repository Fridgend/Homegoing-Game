import pygame
import os
import subprocess
import sys

from src.asset_manager import AssetManager
from src.camera import Camera
from src.config import Config
from src.dialogue import Dialogue
from src.entity import Entity
from src.event import DispatchChain
from src.interactable import Interactable
from src.map_element import MapElement
from src.player import Player
from src.scene_in_out import SceneEntrance, SceneExit
from src.trigger import Trigger
from src.ui_manager import UIManager
from src.event import SceneState
from src.route_tracker import Flags

BACKGROUND_MUSIC_FADE_MS = 1000

class Scene:
    def __init__(self, void_color: tuple[int, int, int, int], bounds: pygame.Vector2,
                 background_music: pygame.mixer.Sound,
                 map_elements: list[MapElement],
                 player: Player,
                 entities: dict[str, Entity],
                 triggers: dict[str, Trigger],
                 entrances: dict[str, SceneEntrance],
                 exits: list[SceneExit]
                 ):
        self.void_color: tuple[int, int, int, int] = void_color
        self.background_music: pygame.mixer.Sound = background_music
        self.bounds: pygame.Vector2 = bounds

        self.map_elements: list[MapElement] = map_elements

        self.player: Player = player
        self.entities_dict: dict[str, Entity] = entities
        self.entities: list[Entity] = []
        self.entities.append(self.player)
        self.dialogue: Dialogue | None = None

        self.triggers: dict[str, Trigger] = triggers

        self.entrances: dict[str, SceneEntrance] = entrances
        self.entering_through: SceneEntrance | None = None
        self.exits: list[SceneExit] = exits
        self.exiting_through: SceneExit | None = None

        self.state: SceneState = SceneState.EXITED
        self.has_loaded_prev: bool = False
        self.void_surface = pygame.Surface(Config.WINDOW_DIMS).convert()
        self.void_surface.fill(self.void_color[:3])
        self.void_surface.set_alpha(self.void_color[3])
        self.background_surface: pygame.Surface = self._build_background()

        self.dispatch_chains: set[DispatchChain] = set()
        self.added_dispatch_chains: set[DispatchChain] = set()
        self.removed_dispatch_chains: set[DispatchChain] = set()

        self.attack_choice_active: bool = False
        self.attack_choice_index: int = 0
        self.attack_choice_input_block: bool = False
        self.attack_choice_paths: tuple[str, str] = ("", "")
        self.attack_choice_title: str = "The village is being attacked!"
        self.choice_font = AssetManager.get_font("snake46") or pygame.font.Font(None, 46)
        self.choice_title_font = AssetManager.get_font("snake64") or pygame.font.Font(None, 64)

    def start_attack_choice(self, peace_path: str, war_path: str) -> None:
        self.attack_choice_paths = (peace_path, war_path)
        self.attack_choice_index = 0
        self.attack_choice_input_block = False
        self.attack_choice_active = True

    def _confirm_attack_choice(self) -> None:
        path = self.attack_choice_paths[self.attack_choice_index]
        if path != "":
            abs_path = os.path.abspath(path)
            try:
                proc = subprocess.Popen([sys.executable, abs_path])
                wait_clock = pygame.time.Clock()
                while proc.poll() is None:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pass

                    surface = pygame.display.get_surface()
                    if surface is not None:
                        surface.fill((0, 0, 0))
                        title = self.choice_title_font.render("Loading next part...", True, (255, 220, 120))
                        hint = self.choice_font.render("Please wait", True, (220, 220, 220))
                        title_rect = title.get_rect(center=(Config.WINDOW_DIMS.x // 2, Config.WINDOW_DIMS.y // 2 - 24))
                        hint_rect = hint.get_rect(center=(Config.WINDOW_DIMS.x // 2, Config.WINDOW_DIMS.y // 2 + 28))
                        surface.blit(title, title_rect)
                        surface.blit(hint, hint_rect)
                        pygame.display.flip()

                    wait_clock.tick(60)
            except Exception:
                subprocess.run([sys.executable, abs_path], check=False)
        Flags.modify(flag="INTRO_ATTACK_CHOICE_DONE", how="add")
        self.attack_choice_active = False
        pygame.quit()
        sys.exit()

    def _build_background(self) -> pygame.Surface:
        world_w = max(int(self.bounds.x * Config.TILE_SIZE), int(Config.WINDOW_DIMS.x))
        world_h = max(int(self.bounds.y * Config.TILE_SIZE), int(Config.WINDOW_DIMS.y))
        try:
            image = pygame.image.load("assets/images/Copilot_20260212_213420.png").convert()
            return pygame.transform.scale(image, (world_w, world_h))
        except Exception:
            bg = pygame.Surface((world_w, world_h)).convert()
            bg.fill(self.void_color[:3])
            return bg

    def add_dispatch_chain(self, chain: DispatchChain):
        self.added_dispatch_chains.add(chain)
        chain.start(self)

    def remove_dispatch_chain(self, chain: DispatchChain):
        self.removed_dispatch_chains.add(chain)

    def load(self, entrance: str, player_face_dir: pygame.Vector2, from_continue: bool) -> None:
        if self.state != SceneState.EXITED: return
        self.state = SceneState.ENTERED
        self.background_music.play(loops=-1, fade_ms=BACKGROUND_MUSIC_FADE_MS)

        if from_continue:
            return

        Camera.TRACK = self.player

        if self.entrances.get(entrance, None) is not None:
            self.player.grid_pos = self.entrances.get(entrance).spawn.copy()
            self.entering_through = self.entrances.get(entrance)
            self.state = SceneState.ENTERING
        self.player.pos = self.player.grid_pos * Config.TILE_SIZE
        self.player.facing = player_face_dir.copy()

        if self.has_loaded_prev:
            return

        for _, entity in self.entities_dict.items():
            if entity.load():
                self.entities.append(entity)

        self.has_loaded_prev = True

    def unload(self) -> None:
        self.state = SceneState.EXITED
        self.background_music.fadeout(BACKGROUND_MUSIC_FADE_MS)

    def input(self, ui_manager: UIManager, keys: pygame.key.ScancodeWrapper) -> None:
        if self.attack_choice_active:
            moving = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN]
            confirming = keys[pygame.K_RETURN] or keys[pygame.K_SPACE]

            if self.attack_choice_input_block:
                if not moving and not confirming:
                    self.attack_choice_input_block = False
                return

            if keys[pygame.K_LEFT] or keys[pygame.K_UP]:
                self.attack_choice_index = (self.attack_choice_index - 1) % 2
                self.attack_choice_input_block = True
                return
            if keys[pygame.K_RIGHT] or keys[pygame.K_DOWN]:
                self.attack_choice_index = (self.attack_choice_index + 1) % 2
                self.attack_choice_input_block = True
                return
            if confirming:
                self._confirm_attack_choice()
                self.attack_choice_input_block = True
            return

        if self.dialogue is not None:
            self.dialogue.input(self, keys)
            ui_manager.input(keys)
            return

        if self.player.controls_disabled:
            return

        self.player.input(keys)

        if not (keys[pygame.K_SPACE] or keys[pygame.K_RETURN]): return
        for entity in self.entities:
            if isinstance(entity, Player):
                continue
            entity.input(keys)
            if isinstance(entity, Interactable) and entity.can_interact(self.player):
                self.dialogue = entity.interact(self.player)
                if self.dialogue is not None:
                    if self.dialogue.start(self):
                        self.dialogue = None
                    else:
                        self.background_music.set_volume(self.background_music.get_volume() / 3)

        for scene_exit in self.exits:
            if not scene_exit.available():
                continue
            if scene_exit.can_interact(self.player):
                self.exiting_through = scene_exit
                self.state = SceneState.EXITING
                break

    def update(self, ui_manager: UIManager, dt: float, manager) -> None:
        Camera.update(self.bounds, dt)

        if self.state == SceneState.EXITED:
            if self.exiting_through is None:
                return
            manager.load_scene(self.exiting_through.next_scene,
                               self.exiting_through.next_entrance,
                               self.player.facing)
            self.exiting_through = None
            return

        self.dispatch_chains.update(self.added_dispatch_chains)
        self.added_dispatch_chains.clear()
        for chain in self.dispatch_chains:
            chain.update(self, dt)
        self.dispatch_chains = self.dispatch_chains.difference(self.removed_dispatch_chains)
        self.removed_dispatch_chains.clear()

        for _, trigger in self.triggers.items():
            if trigger.catch(self):
                trigger.dispatch(self)

        if self.entering_through is not None:
            self.entering_through.update(manager, dt)
            if self.entering_through.complete:
                self.entering_through.complete = False
                self.entering_through = None
                self.state = SceneState.ENTERED

        elif self.exiting_through is not None:
            self.exiting_through.update(manager, dt)
            if self.exiting_through.complete:
                self.exiting_through.complete = False
                self.state = SceneState.EXITED
            return

        self.player.update(self.entities, self.map_elements, ui_manager, dt)
        self.player.grid_pos.x = pygame.math.clamp(self.player.grid_pos.x, 0, self.bounds.x)
        self.player.grid_pos.y = pygame.math.clamp(self.player.grid_pos.y, 0, self.bounds.y)
        self.player.pos.x = pygame.math.clamp(self.player.pos.x, 0,
                                              self.bounds.x * Config.TILE_SIZE - self.player.sprite.dimensions.x)
        self.player.pos.y = pygame.math.clamp(self.player.pos.y, 0,
                                              self.bounds.y * Config.TILE_SIZE - self.player.sprite.dimensions.y)

        for scene_exit in self.exits:
            if not scene_exit.available():
                continue
            if scene_exit.entered(self.player.grid_pos):
                self.exiting_through = scene_exit
                self.state = SceneState.EXITING
                break

        if self.dialogue is not None:
            self.dialogue.update(ui_manager, self, dt)
            if self.dialogue.fade == 0:
                self.dialogue.reset()
                self.dialogue = None
                self.background_music.set_volume(self.background_music.get_volume() * 3)

        ui_manager.update()

        for entity in self.entities:
            if isinstance(entity, Player):
                continue
            entity.update(self.entities, self.map_elements, ui_manager, dt)

    def render(self, window_surface: pygame.Surface, ui_manager: UIManager) -> None:
        window_surface.fill((0, 0, 0))
        window_surface.blit(self.background_surface, Camera.world_pos_to_view_pos(pygame.Vector2(0, 0)))
        for map_element in self.map_elements: map_element.render(window_surface)
        for entity in self.entities:
            if isinstance(entity, Player):
                continue
            entity.render(window_surface)
        self.player.render(window_surface)

        if self.dialogue is not None:
            dims: pygame.Rect = pygame.Rect(
                Config.DIALOGUE_BOX_POS.x, Config.DIALOGUE_BOX_POS.y,
                Config.DIALOGUE_BOX_DIMS.x, Config.DIALOGUE_BOX_DIMS.y
            )

            self.dialogue.render(window_surface, dims, ui_manager)

        if self.attack_choice_active:
            overlay = pygame.Surface(Config.WINDOW_DIMS).convert_alpha()
            overlay.fill((0, 0, 0, 190))
            window_surface.blit(overlay, (0, 0))

            panel_w = int(Config.WINDOW_DIMS.x * 0.82)
            panel_h = int(Config.WINDOW_DIMS.y * 0.5)
            panel_x = (int(Config.WINDOW_DIMS.x) - panel_w) // 2
            panel_y = (int(Config.WINDOW_DIMS.y) - panel_h) // 2

            pygame.draw.rect(window_surface, (20, 20, 24), (panel_x, panel_y, panel_w, panel_h), border_radius=14)
            pygame.draw.rect(window_surface, (230, 230, 230), (panel_x, panel_y, panel_w, panel_h), width=3, border_radius=14)

            title = self.choice_title_font.render(self.attack_choice_title, True, (255, 220, 120))
            title_rect = title.get_rect(center=(panel_x + panel_w // 2, panel_y + int(panel_h * 0.28)))
            window_surface.blit(title, title_rect)

            options = ["Escape", "Escape and fight back"]
            for i, text in enumerate(options):
                selected = i == self.attack_choice_index
                color = (255, 255, 255) if selected else (170, 170, 170)
                opt = self.choice_font.render(text, True, color)
                opt_rect = opt.get_rect(center=(panel_x + panel_w // 2, panel_y + int(panel_h * (0.58 + 0.20 * i))))
                window_surface.blit(opt, opt_rect)

                if selected:
                    pygame.draw.rect(window_surface, (255, 215, 90),
                                     (opt_rect.x - 14, opt_rect.y - 8, opt_rect.width + 28, opt_rect.height + 16),
                                     width=2, border_radius=10)
