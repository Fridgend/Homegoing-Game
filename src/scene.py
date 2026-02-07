import enum

import pygame

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

BACKGROUND_MUSIC_FADE_MS = 1000

class SceneState(enum.Enum):
    ENTERING = 0
    ENTERED = 1
    EXITING = 2
    EXITED = 3

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

        self.dispatch_chains: set[DispatchChain] = set()
        self.added_dispatch_chains: set[DispatchChain] = set()
        self.removed_dispatch_chains: set[DispatchChain] = set()

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
        window_surface.blit(self.void_surface, (0, 0))
        for entity in self.entities:
            if isinstance(entity, Player):
                continue
            entity.render(window_surface)
        for map_element in self.map_elements: map_element.render(window_surface)
        self.player.render(window_surface)

        if self.dialogue is not None:
            dims: pygame.Rect = pygame.Rect(
                Config.DIALOGUE_BOX_POS.x, Config.DIALOGUE_BOX_POS.y,
                Config.DIALOGUE_BOX_DIMS.x, Config.DIALOGUE_BOX_DIMS.y
            )

            self.dialogue.render(window_surface, dims, ui_manager)