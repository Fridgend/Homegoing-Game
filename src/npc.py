import pygame

from src.config import Config
from src.dialogue import Dialogue
from src.entity import Entity
from src.entity_route import EntityRoute
from src.interactable import Interactable
from src.map_element import MapElement
from src.player import Player
from src.route_tracker import Conditions
from src.sprite import Sprite, dir_to_str
from src.ui_manager import UIManager


class NPC(Entity, Interactable):
    def __init__(self, sprite: Sprite, collision: bool, spawn: pygame.Vector2, conditions: Conditions,
                 routes: dict[str, EntityRoute], dialogues: dict[str, Dialogue]):
        Entity.__init__(self, sprite, collision, spawn, conditions, routes)
        Interactable.__init__(self)

        self.dialogues: dict[str, Dialogue] = dialogues
        self.current_dialogue: str | None = None

    def can_interact(self, player: Player) -> bool:
        return pygame.Rect(self.grid_pos, self.hit_box).collidepoint(player.grid_pos + player.facing)
    
    def interact(self, player: Player, dialogue: str | None = None) -> Dialogue | None:
        if self.block:
            return None

        if dialogue is None:
            for k, v in self.dialogues.items():
                if v.conditions.satisfied():
                    self.current_dialogue = k
                    break

            if self.current_dialogue is None:
                return None
        else:
            self.current_dialogue = dialogue

        self.look_at(player.grid_pos)
        self.block = True
        return self.dialogues.get(self.current_dialogue, None)

    def input(self, keys: pygame.key.ScancodeWrapper) -> None:
        pass

    def update(self, entities: list[Entity], map_elements: list[MapElement], ui_manager: UIManager, dt: float)\
            -> None:
        if self.waypoint_wait_time != 0:
            self.waypoint_wait_time -= dt
            if self.waypoint_wait_time < 0:
                self.waypoint_wait_time = 0

        if not self.moving and self.waypoint_wait_time == 0 and self.current_route is not None:
            dx: int = int(pygame.math.clamp(
                self.routes.get(self.current_route).waypoints[self.route_waypoint].pos.x - self.grid_pos.x, -1, 1))
            dy: int = int(pygame.math.clamp(
                self.routes.get(self.current_route).waypoints[self.route_waypoint].pos.y - self.grid_pos.y, -1, 1))

            if dx != 0:
                dy = 0

            if dx != 0 or dy != 0:
                self.velocity = pygame.Vector2(dx, dy)
                self.facing = self.routes.get(self.current_route).waypoints[self.route_waypoint].face_dir
                self.moving = True
                self.move_time = 0.0
            else:
                self.waypoint_wait_time = self.routes.get(self.current_route).waypoints[self.route_waypoint].wait
                self.route_waypoint += 1
                if self.route_waypoint >= len(self.routes.get(self.current_route).waypoints):
                    self.route_waypoint = 0
                    self.current_route = None

        if self.moving:
            target_grid_pos: pygame.Vector2 = self.grid_pos + self.velocity

            collision: bool = False
            rect: pygame.Rect = pygame.Rect(target_grid_pos, self.hit_box)
            for entity in entities:
                if entity.get_collision(rect):
                    self.moving = False
                    self.velocity = pygame.Vector2(0, 0)
                    self.move_time = 0
                    collision = True
                    break

            for map_element in map_elements:
                if map_element.get_collision(rect):
                    self.grid_pos = self.routes.get(self.current_route).waypoints[self.route_waypoint].pos
                    self.pos = self.grid_pos * Config.TILE_SIZE
                    self.moving = False
                    self.velocity = pygame.Vector2(0, 0)
                    self.move_time = 0
                    collision = True
                    break

            if not collision:
                self.move_time += dt
                t: float = min(
                    self.move_time / self.routes.get(self.current_route).waypoints[self.route_waypoint].speed, 1.0)

                start_pos: pygame.Vector2 = self.grid_pos * Config.TILE_SIZE
                target_pos: pygame.Vector2 = target_grid_pos * Config.TILE_SIZE

                self.pos = start_pos.lerp(target_pos, t)

                if t >= 1.0:
                    self.grid_pos += self.velocity
                    self.velocity = pygame.Vector2(0, 0)
                    self.moving = False

        if self.current_route is not None and self.moving:
            self.sprite.set(dir_to_str(self.facing, self.facing))
        else:
            self.sprite.set(dir_to_str(self.velocity, self.facing))

        self.sprite.update(dt)
        if self.block and (self.dialogues.get(self.current_dialogue, None) is None or
                           not self.dialogues.get(self.current_dialogue).playing):
            self.elapsed_time += dt
            if self.elapsed_time > 1:
                self.elapsed_time = 0
                self.block = False