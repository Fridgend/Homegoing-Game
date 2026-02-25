import pygame
import random
import math

from src.asset_manager import AssetManager
from src.game_backends.backend import Backend, GameState
from src.ui_manager import Text

from src.config import Config

TREE_OFFSET = pygame.Vector2(26, 40)

def draw_pixel_tree():
    s = pygame.Surface((64, 80), pygame.SRCALPHA)
    pygame.draw.rect(s, (80, 50, 20), (TREE_OFFSET.x, TREE_OFFSET.y, 12, 40))
    pygame.draw.circle(s, (20, 80, 20), (32, 30), 28) 
    pygame.draw.circle(s, (10, 60, 10), (15, 35), 18)
    pygame.draw.circle(s, (10, 60, 10), (50, 35), 18)
    return s

class EscapeGameBackend(Backend):
    def __init__(self):
        super().__init__()

        self.esi_sprite = AssetManager.get_image("esi_spritesheet")
        self.move_speed = 5
        self.can_escape = False

        self.raider_sprite = AssetManager.get_image("warrior_spritesheet")
        self.tree_sprite = draw_pixel_tree()
        self.background_surface = self._build_background()
        
        self.player_rect = pygame.Rect(50, 280, 22, 26)
        self.player_velocity = pygame.Vector2(0, 0)
        self.max_player_x = 50

        self.camera_x = 50
        self.world_width = 12000
        
        self.trees = []

        self.raiders = []
        self.spawn_timer = 0

        self.run_screen = True
        self.next_scene_escaped = ""
        self.next_scene_captured = ""

    def set_params(self, params):
        self.spawn_timer = params.get("first_spawn", 0)
        self.can_escape = params.get("can_win", False)
        self.next_scene_escaped = params.get("next_scene_escaped", "")
        self.next_scene_captured = params.get("next_scene_captured", "")

    def init(self, game) -> None:
        self.next_backend = None
        self.fade = 255
        self.fading = 500

        self.overlay.fill((0, 0, 0))

    def unload(self, game) -> None:
        pass

    def input(self, game) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
                return

            if self.fading != 0 and self.fade != 0 and self.fade != 255:
                continue

        if self.fading != 0 and self.fade != 0 and self.fade != 255: return

        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        if self.run_screen:
            if keys[pygame.K_RETURN] or keys[pygame.K_SPACE]:
                self.run_screen = False
            return

        dx, dy = 0, 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -self.move_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = self.move_speed
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -self.move_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = self.move_speed

        self.player_velocity = pygame.Vector2(dx, dy)

    def update(self, game) -> None:
        self.fade = max(0, min(255, int(self.fade - self.fading * game.delta_time)))
        if self.next_backend and self.fade == 255:
            if self.next_backend == GameState.QUITTING:
                game.running = False
                return
            game.set_backend(self.next_backend)

        if self.run_screen:
            return

        self.move_with_collision(self.player_rect, self.player_velocity.x, self.player_velocity.y)
        self.player_rect.x = pygame.math.clamp(self.player_rect.x, 0, self.player_rect.x)
        self.player_rect.y = pygame.math.clamp(self.player_rect.y, 0, Config.WINDOW_DIMS.y)

        self.spawn_timer -= game.delta_time
        if self.spawn_timer <= 0:
            self._spawn_raider()
            self.spawn_timer = 1

        for r in self.raiders:
            dx = self.player_rect.centerx - r["pos"].x
            dy = self.player_rect.centery - r["pos"].y
            dist = math.hypot(dx, dy)
            if dist != 0:
                rdx = r["speed"] * dx / dist
                rdy = r["speed"] * dy / dist
                self.move_with_collision(r["rect"], rdx, rdy)
                r["pos"].update(r["rect"].centerx, r["rect"].centery)

            if r["rect"].colliderect(self.player_rect):
                game.scene_manager.load_scene(self.next_scene_captured, "main", pygame.Vector2(0, 1))
                self.next_backend = GameState.PLAYING
                self.fading = -175
                self.player_velocity = pygame.Vector2(0, 0)
                return

        self.raiders = [
            r for r in self.raiders
            if self.player_rect.centerx - Config.WINDOW_DIMS.x // 2 <= r["rect"].x <= self.player_rect.centerx + Config.WINDOW_DIMS.x // 2
               and -100 <= r["rect"].y <= Config.WINDOW_DIMS.y + 100
        ]

        if math.fabs(self.player_rect.x - self.max_player_x) >= 40:
            self.max_player_x = self.player_rect.x
            self._spawn_tree()

        self.camera_x = self.player_rect.centerx - Config.WINDOW_DIMS.x // 2

    def render(self, game) -> None:
        if self.run_screen:
            self._show_run(game)
        else:
            scaled_bg = pygame.transform.scale(self.background_surface, Config.WINDOW_DIMS)
            game.window_surface.blit(scaled_bg, (0, 0))

            for tree_hitbox in self.trees:
                if tree_hitbox.x < (self.camera_x - Config.WINDOW_DIMS.x // 2) - TREE_OFFSET.x:
                    continue
                game.window_surface.blit(
                    self.tree_sprite,
                    (tree_hitbox.x - TREE_OFFSET.x - self.camera_x, tree_hitbox.y - TREE_OFFSET.y)
                )

            game.window_surface.blit(self.esi_sprite, (self.player_rect.x - self.camera_x, self.player_rect.y))

            for r in self.raiders:
                game.window_surface.blit(self.raider_sprite, (r["rect"].x - self.camera_x, r["rect"].y))

            if self.can_escape and self.player_rect.x > self.world_width:
                game.scene_manager.load_scene(self.next_scene_escaped, "main", pygame.Vector2(0, 1))
                self.next_backend = GameState.PLAYING
                self.fading = -400
                return

        if self.fade > 0:
            self.overlay.set_alpha(self.fade)
            game.window_surface.blit(self.overlay, (0, 0))

        pygame.display.flip()

    def _spawn_tree(self):
        x = random.randint(50, 100)
        y = random.randint(50, Config.WINDOW_DIMS.y - 100)
        self.trees.append(pygame.Rect(
            x + self.player_rect.x + Config.WINDOW_DIMS.x / 2 + TREE_OFFSET.x,
            y + TREE_OFFSET.y,
            12, 30
        ))

    def _show_run(self, game):
        game.window_surface.fill((0, 0, 0))
        game.ui_manager.draw_text(Text(
            text="RUN",
            color=[255, 255, 255, 255],
            pos=Config.WINDOW_DIMS // 2,
            font=AssetManager.get_font("snake64"),
            align_center=True
        ), game.window_surface)

    def _build_background(self):
        bg_dims = Config.WINDOW_DIMS * 2
        bg = pygame.Surface(bg_dims)
        bg.fill((210, 190, 150))  # Sand
        pygame.draw.rect(bg, (30, 100, 200), (0, 0, bg_dims.x, int(bg_dims.y * 0.1)))  # Ocean
        return bg

    def _spawn_raider(self):
        edge = random.choice(['LEFT', 'TOP', 'BOTTOM', 'RIGHT'])
        if edge == 'LEFT':
            x, y = self.camera_x - 40, random.randint(0, Config.WINDOW_DIMS.y)
        elif edge == 'RIGHT':
            x, y = self.camera_x + Config.WINDOW_DIMS.x + 40, random.randint(0, Config.WINDOW_DIMS.y)
        elif edge == 'TOP':
            x, y = random.randint(self.camera_x, self.camera_x + Config.WINDOW_DIMS.x), -40
        else:
            x, y = random.randint(self.camera_x, self.camera_x + Config.WINDOW_DIMS.x), Config.WINDOW_DIMS.y + 40
        
        if len(self.raiders) >= 30:
            self.raiders.pop(0)
        rect = pygame.Rect(x, y, 24, 28)
        self.raiders.append({
            "rect": rect,
            "pos": pygame.Vector2(rect.centerx, rect.centery),
            "speed": random.uniform(4.5 if self.can_escape else 4, 5.5 if self.can_escape else 6)
        })

    def move_with_collision(self, rect, dx, dy):
        rect.x += dx
        for tree in self.trees:
            if rect.colliderect(tree):
                if dx > 0: rect.right = tree.left
                if dx < 0: rect.left = tree.right
        
        rect.y += dy
        for tree in self.trees:
            if rect.colliderect(tree):
                if dy > 0: rect.bottom = tree.top
                if dy < 0: rect.top = tree.bottom

    def _reset(self):
        self.player_rect.x = 50
        self.player_rect.y = 280
        self.raiders = []
        self.trees = []
        self.spawn_timer = 3