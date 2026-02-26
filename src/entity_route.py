import pygame

from src.route_tracker import Conditions

class Waypoint:
    def __init__(self, pos: pygame.Vector2, speed: float, face_dir: pygame.Vector2, wait: float):
        self.pos: pygame.Vector2 = pos
        self.speed: float = speed
        self.face_dir: pygame.Vector2 = face_dir
        self.wait: float = wait

class EntityRoute:
    def __init__(self, waypoints: list[Waypoint], conditions: Conditions):
        self.waypoints: list[Waypoint] = waypoints
        self.conditions: Conditions = conditions