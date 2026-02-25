import enum

import pygame

from src.player import Player
from src.route_tracker import Conditions


class SceneTransition(enum.Enum):
    FADE = 0
    TELEPORT = 1

def str_to_scene_transition(string: str) -> SceneTransition | None:
    match string:
        case "fade":
            return SceneTransition.FADE
        case "no transition":
            return SceneTransition.TELEPORT
        case _:
            return None

class SceneEntrance:
    def __init__(self, spawn: pygame.Vector2,
                 transition: SceneTransition, transition_time: float):
        self.spawn: pygame.Vector2 = spawn
        self.transition: SceneTransition = transition
        self.transition_time: float = transition_time

        self.fade_step: float = 255.0 / max(transition_time, 0.001)
        self.complete: bool = False

    def update(self, manager, dt: float) -> None:
        match self.transition:
            case SceneTransition.FADE:
                manager.fade = pygame.math.clamp(manager.fade - self.fade_step * dt, 0, 255)
                if manager.fade == 0:
                    self.complete = True
            case SceneTransition.TELEPORT:
                manager.fade = 0
                self.complete = True

class SceneExit:
    def __init__(self, rect: pygame.Rect, require_interact: bool,
                 transition: SceneTransition | None, transition_time: float,
                 next_scene: str, next_entrance: str, conditions: Conditions):
        self.rect: pygame.Rect = rect
        self.require_interact: bool = require_interact
        self.transition: SceneTransition | None = transition
        self.transition_time: float = transition_time
        self.next_scene: str = next_scene
        self.next_entrance: str = next_entrance
        self.conditions: Conditions = conditions

        self.fade_step: float = 255.0 / max(transition_time, 0.001)
        self.complete: bool = False

    def available(self) -> bool:
        return self.conditions.satisfied()

    def entered(self, player_grid_pos: pygame.Vector2) -> bool:
        return not self.require_interact and self.rect.collidepoint(player_grid_pos)

    def can_interact(self, player: Player) -> bool:
        return self.rect.collidepoint(player.grid_pos + player.facing)

    def update(self, manager, dt: float) -> None:
        match self.transition:
            case SceneTransition.FADE:
                manager.fade = pygame.math.clamp(manager.fade + self.fade_step * dt, 0, 255)
                if manager.fade == 255:
                    self.complete = True
            case SceneTransition.TELEPORT:
                self.complete = True
            case _:
                self.complete = True