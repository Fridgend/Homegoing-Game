import pygame

from src.asset_manager import AssetManager
from src.camera import Camera
from src.config import Config
from src.entity import Entity
from src.map_element import MapElement
from src.route_tracker import Conditions
from src.sprite import Sprite
from src.sprite import dir_to_str
from src.ui_manager import UIManager


class Player(Entity):
    def __init__(self, spawn: pygame.Vector2, sprite: Sprite, move_duration: float):
        super().__init__(sprite, True, spawn, Conditions([], [], []), {})

        self.move_duration: float = move_duration
        self.controls_disabled: bool = False

    def set_sprite(self, sprite: Sprite, hit_box: pygame.Vector2) -> None:
        self.sprite = sprite
        self.hit_box = hit_box
        self.pos = self.grid_pos * Config.TILE_SIZE

    def input(self, keys: pygame.key.ScancodeWrapper) -> None:
        if self.moving:
            return
        
        dx: int = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy: int = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])

        if dx != 0:
            dy = 0

        if dx != 0 or dy != 0:
            self.velocity = pygame.Vector2(dx, dy)
            self.facing = self.velocity
            self.moving = True

    def update(self, entities: list[Entity], map_elements: list[MapElement], ui_manager: UIManager, dt: float)\
            -> None:
        self.sprite.set(dir_to_str(self.velocity, self.facing))
        self.sprite.update(dt)

        if self.controls_disabled:
            self.move_waypoints(dt)

        if not self.moving:
            return

        target_grid_pos: pygame.Vector2 = self.grid_pos + self.velocity
        rect: pygame.Rect = pygame.Rect(target_grid_pos, self.hit_box)
        for entity in entities:
            if entity.get_collision(rect):
                self.moving = False
                self.velocity = pygame.Vector2(0, 0)
                self.move_time = 0
                return

        for map_element in map_elements:
            if map_element.get_collision(rect):
                self.moving = False
                self.velocity = pygame.Vector2(0, 0)
                self.move_time = 0
                return
        
        self.move_time += dt
        t: float = min(self.move_time / self.move_duration, 1.0)

        start_pos: pygame.Vector2 = self.grid_pos * Config.TILE_SIZE
        target_pos: pygame.Vector2 = target_grid_pos * Config.TILE_SIZE

        self.pos = start_pos.lerp(target_pos, t)

        if t >= 1.0:
            self.grid_pos += self.velocity
            self.velocity = pygame.Vector2(0, 0)
            self.moving = False
            self.move_time = 0

    def move_waypoints(self, dt: float):
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
            else:
                self.waypoint_wait_time = self.routes.get(self.current_route).waypoints[self.route_waypoint].wait
                self.route_waypoint += 1
                if self.route_waypoint >= len(self.routes.get(self.current_route).waypoints):
                    self.route_waypoint = 0
                    self.current_route = None
        elif self.current_route is None and self.waypoint_wait_time == 0:
            self.controls_disabled = False

    def render(self, surface: pygame.Surface) -> None:
        centered: pygame.Vector2 = self.pos - self.sprite.dimensions / 2
        surface.blit(self.sprite.get() or AssetManager.NULL_IMAGE, Camera.world_pos_to_view_pos(centered))