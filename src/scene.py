import pygame
import random

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

BACKGROUND_MUSIC_FADE_MS = 1000

class Scene:
    def __init__(self, void_color: tuple[int, int, int, int], bounds: pygame.Vector2,
                 background_music: pygame.mixer.Sound | None,
                 map_elements: list[MapElement],
                 player: Player,
                 entities: dict[str, Entity],
                 triggers: dict[str, Trigger],
                 entrances: dict[str, SceneEntrance],
                 exits: list[SceneExit]
                 ):
        self.void_color: tuple[int, int, int, int] = void_color
        self.background_music: pygame.mixer.Sound | None = background_music
        self.music_base_volume: float = 0 if background_music is None else background_music.get_volume()
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
        self.render_generated_background: bool = self._needs_generated_background()
        self.background_tile: pygame.Surface | None = self._build_sand_background_tile() \
            if self.render_generated_background else None

        self.dispatch_chains: set[DispatchChain] = set()
        self.added_dispatch_chains: set[DispatchChain] = set()
        self.removed_dispatch_chains: set[DispatchChain] = set()

    def set_music_volume(self, volume: float) -> None:
        if self.background_music is None:
            return
        self.background_music.set_volume(self.music_base_volume * volume)

    def add_dispatch_chain(self, manager, chain: DispatchChain):
        self.added_dispatch_chains.add(chain)
        chain.start(self, manager)

    def remove_dispatch_chain(self, chain: DispatchChain):
        self.removed_dispatch_chains.add(chain)

    def load(self, entrance: str, player_face_dir: pygame.Vector2, same_bg_music: bool, from_continue: bool) -> None:
        if self.state != SceneState.EXITED: return
        self.state = SceneState.ENTERED

        if not same_bg_music and self.background_music is not None:
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

    def unload(self, same_bg_music: bool) -> None:
        self.state = SceneState.EXITED
        if not same_bg_music and self.background_music is not None:
            self.background_music.fadeout(BACKGROUND_MUSIC_FADE_MS)

    def input(self, ui_manager: UIManager, manager, keys: pygame.key.ScancodeWrapper) -> None:
        if self.dialogue is not None:
            self.dialogue.input(self, manager, keys)
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
                    if self.dialogue.start(self, manager):
                        self.dialogue = None
                    elif self.background_music is not None:
                        self.music_base_volume /= 3
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
            chain.update(self, manager, dt)
        self.dispatch_chains = self.dispatch_chains.difference(self.removed_dispatch_chains)
        self.removed_dispatch_chains.clear()

        for _, trigger in self.triggers.items():
            if trigger.catch(self):
                trigger.dispatch(manager, self)

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
        if self.player.pos.x > self.bounds.x * Config.TILE_SIZE or \
           self.player.pos.y > self.bounds.y * Config.TILE_SIZE:
            self.player.grid_pos.x = pygame.math.clamp(self.player.grid_pos.x, 0, self.bounds.x)
            self.player.grid_pos.y = pygame.math.clamp(self.player.grid_pos.y, 0, self.bounds.y)
            self.player.pos.x = self.player.grid_pos.x * Config.TILE_SIZE
            self.player.pos.y = self.player.grid_pos.y * Config.TILE_SIZE

            self.player.velocity = pygame.Vector2(0, 0)
            self.player.moving = False
            self.player.move_time = 0

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
                if self.background_music is not None:
                    self.music_base_volume *= 3
                    self.background_music.set_volume(self.background_music.get_volume() * 3)

        ui_manager.update()

        for entity in self.entities:
            if isinstance(entity, Player):
                continue
            entity.update(self.entities, self.map_elements, ui_manager, dt)

    def render(self, window_surface: pygame.Surface, ui_manager: UIManager) -> None:
        if self.render_generated_background and self.background_tile is not None:
            self._render_tiled_background(window_surface)
        else:
            window_surface.fill((0, 0, 0))
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

    def _needs_generated_background(self) -> bool:
        world_w = int(self.bounds.x * Config.TILE_SIZE)
        world_h = int(self.bounds.y * Config.TILE_SIZE)
        win_w = int(Config.WINDOW_DIMS.x)
        win_h = int(Config.WINDOW_DIMS.y)
        return world_w < win_w or world_h < win_h

    def _render_tiled_background(self, window_surface: pygame.Surface) -> None:
        tile_w, tile_h = self.background_tile.get_size()
        win_w = int(Config.WINDOW_DIMS.x)
        win_h = int(Config.WINDOW_DIMS.y)
        offset_x = -int(Camera.POS.x) % tile_w
        offset_y = -int(Camera.POS.y) % tile_h

        for x in range(-tile_w, win_w + tile_w, tile_w):
            for y in range(-tile_h, win_h + tile_h, tile_h):
                window_surface.blit(self.background_tile, (x + offset_x, y + offset_y))

    def _build_sand_background_tile(self) -> pygame.Surface:
        tile_size = 8
        pixel_w = 32
        pixel_h = 32
        surface = pygame.Surface((pixel_w * tile_size, pixel_h * tile_size)).convert()
        rng = random.Random(int(self.bounds.x * 19 + self.bounds.y * 31))

        base_palette = [
            (184, 156, 108),
            (198, 172, 124),
            (210, 186, 140),
            (222, 200, 156)
        ]

        for x in range(pixel_w):
            for y in range(pixel_h):
                color = base_palette[min(len(base_palette) - 1, int((y / pixel_h) * len(base_palette)))]
                jitter = rng.randint(-10, 10)
                px = (
                    max(0, min(255, color[0] + jitter)),
                    max(0, min(255, color[1] + jitter)),
                    max(0, min(255, color[2] + jitter))
                )
                pygame.draw.rect(surface, px, (x * tile_size, y * tile_size, tile_size, tile_size))

                if rng.random() < 0.05:
                    dark = (max(0, px[0] - 22), max(0, px[1] - 22), max(0, px[2] - 22))
                    pygame.draw.rect(surface, dark, (x * tile_size, y * tile_size, tile_size // 2, tile_size // 2))

        return surface
