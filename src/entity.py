import pygame

from src.asset_manager import AssetManager
from src.camera import Camera
from src.config import Config
from src.entity_route import EntityRoute
from src.map_element import MapElement
from src.route_tracker import Conditions
from src.sprite import Sprite
from src.sprite import dir_to_str
from src.ui_manager import UIManager


class Entity:
    def __init__(self, sprite: Sprite, collision: bool, spawn: pygame.Vector2, conditions: Conditions,
                 routes: dict[str, EntityRoute]):
        self.grid_pos: pygame.Vector2 = spawn.copy()
        self.facing: pygame.Vector2 = pygame.Vector2(0, 1)
        self.velocity: pygame.Vector2 = pygame.Vector2(0, 0)

        self.conditions: Conditions = conditions
        self.routes: dict[str, EntityRoute] = routes
        self.current_route: str | None = None
        self.route_waypoint: int = 0
        self.waypoint_wait_time: float = 0

        self.pos: pygame.Vector2 = spawn * Config.TILE_SIZE
        self.moving: bool = False
        self.move_time: float = 0

        self.sprite: Sprite = sprite
        self.hit_box: pygame.Vector2 = self.sprite.dimensions / Config.TILE_SIZE

        self.collision: bool = collision

    def load(self) -> bool:
        for k, v in self.routes.items():
            if v.conditions.satisfied():
                self.current_route = k
                break
        return self.conditions.satisfied()

    def set_sprite(self, sprite: Sprite, hit_box: pygame.Vector2) -> None:
        self.sprite = sprite
        self.hit_box = hit_box

    def set_route(self, route: str) -> None:
        self.current_route = route
        self.route_waypoint = 0
        self.waypoint_wait_time = 0

    def get_collision(self, rect: pygame.Rect) -> bool:
        return self.collision and rect.colliderect(pygame.Rect(self.grid_pos, self.hit_box))

    def look_at(self, grid_pos: pygame.Vector2) -> None:
        diff: pygame.Vector2 = self.grid_pos - grid_pos
        if diff.x == 0 and diff.y == 0:
            return

        if abs(diff[1]) > abs(diff[0]):
            self.facing = pygame.Vector2(0, -diff[1] / abs(diff[1]))
        else:
            self.facing = pygame.Vector2(-diff[0] / abs(diff[0]), 0)

    def input(self, keys: pygame.key.ScancodeWrapper) -> None:
        pass

    def update(self, entities: list, map_elements: list[MapElement], ui_manager: UIManager, dt: float) -> None:
        if self.waypoint_wait_time != 0:
            self.waypoint_wait_time -= dt
            if self.waypoint_wait_time < 0:
                self.waypoint_wait_time = 0

        if self.current_route is not None and self.waypoint_wait_time == 0:
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

    def render(self, surface: pygame.Surface) -> None:
        centered: pygame.Vector2 = self.pos - self.sprite.dimensions / 2
        surface.blit(self.sprite.get() or AssetManager.NULL_IMAGE, Camera.world_pos_to_view_pos(centered))