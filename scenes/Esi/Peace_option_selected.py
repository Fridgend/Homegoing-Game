import pygame
import torch
import torch.nn as nn
import random
import math
import os

class EnduranceEngine(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(2, 1) 
    def get_speed(self, w, h):
        with torch.no_grad():
            x = torch.tensor([w, h], dtype=torch.float32)
            return 4.0 + (torch.sigmoid(self.fc(x)).item() * 2.5)

def draw_pixel_esi():
    s = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.rect(s, (100, 60, 20), (10, 6, 12, 18)) 
    pygame.draw.rect(s, (255, 200, 0), (10, 18, 12, 8)) 
    pygame.draw.rect(s, (10, 10, 10), (10, 2, 12, 6))   
    return s

def draw_pixel_raider():
    s = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.rect(s, (20, 10, 5), (8, 6, 16, 22))  
    pygame.draw.rect(s, (255, 255, 255), (10, 12, 2, 2)) 
    pygame.draw.rect(s, (255, 255, 255), (20, 12, 2, 2)) 
    return s

def draw_pixel_tree():
    s = pygame.Surface((64, 80), pygame.SRCALPHA)
    pygame.draw.rect(s, (80, 50, 20), (26, 40, 12, 40)) 
    pygame.draw.circle(s, (20, 80, 20), (32, 30), 28) 
    pygame.draw.circle(s, (10, 60, 10), (15, 35), 18)
    pygame.draw.circle(s, (10, 60, 10), (50, 35), 18)
    return s

class EsiEscapeGame:
    def __init__(self, will=1.5, heritage=1.5):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.screen_w, self.screen_h = self.screen.get_size()
        font_path = os.path.join("assets", "fonts", "Snake.ttf")
        self.font = pygame.font.Font(font_path, 64)
        self.sprite_scale = 1.25
        self.tree_offset_x = int(26 * self.sprite_scale)
        self.tree_offset_y = int(40 * self.sprite_scale)
        self.world_width = 12000
        self.world_height = self.screen_h
        self.camera_x = 0
        
        self.engine = EnduranceEngine()
        self.move_speed = self.engine.get_speed(will, heritage) * 1.3
        
        
        self.esi_sprite = self._scale_sprite(draw_pixel_esi())
        self.raider_sprite = self._scale_sprite(draw_pixel_raider())
        self.tree_sprite = self._scale_sprite(draw_pixel_tree())
        self.background_surface = self._build_background()
        
        self.player_rect = pygame.Rect(
            50, 280,
            int(22 * self.sprite_scale),
            int(26 * self.sprite_scale)
        )
        
        self.trees = []
        for _ in range(100):
            tx = random.randint(150, self.world_width - 100)
            ty = random.randint(50, self.world_height - 100)
            self.trees.append(pygame.Rect(
                tx + self.tree_offset_x,
                ty + self.tree_offset_y,
                int(12 * self.sprite_scale),
                int(30 * self.sprite_scale)
            ))

        self.raiders = []
        self.spawn_timer = 0
        self.invincible_timer = 120 # 2 seconds of grace at 60fps        
        self.running = True

    def _scale_sprite(self, surface):
        width = int(surface.get_width() * self.sprite_scale)
        height = int(surface.get_height() * self.sprite_scale)
        return pygame.transform.scale(surface, (width, height))

    def _build_background(self):
        bg_w, bg_h = self.screen_w * 2, self.screen_h * 2
        bg = pygame.Surface((bg_w, bg_h))
        bg.fill((210, 190, 150))  # Sand
        pygame.draw.rect(bg, (30, 100, 200), (0, 0, bg_w, int(bg_h * 0.1)))  # Ocean
        return bg

    def _render_background(self):
        if self.background_surface.get_size() != (self.screen_w * 2, self.screen_h * 2):
            self.background_surface = self._build_background()
        scaled_bg = pygame.transform.scale(self.background_surface, (self.screen_w, self.screen_h))
        self.screen.blit(scaled_bg, (0, 0))

    def spawn_raider(self):
        edge = random.choice(['LEFT', 'TOP', 'BOTTOM', 'RIGHT'])
        if edge == 'LEFT':
            x, y = self.camera_x - 40, random.randint(0, self.world_height)
        elif edge == 'RIGHT':
            x, y = self.camera_x + self.screen_w + 40, random.randint(0, self.world_height)
        elif edge == 'TOP':
            x, y = random.randint(self.camera_x, self.camera_x + self.screen_w), -40
        else:
            x, y = random.randint(self.camera_x, self.camera_x + self.screen_w), self.world_height + 40
        
        if len(self.raiders) >= 30:
            self.raiders.pop(0)
        self.raiders.append({
            "rect": pygame.Rect(
                x, y,
                int(24 * self.sprite_scale),
                int(28 * self.sprite_scale)
            ),
            "speed": random.uniform(3.2, 4.5)
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

    def run(self):
        self.screen.fill((0, 0, 0))
        instruction = "Get to the other side! Fast!"
        words = instruction.split(" ")
        current_text = ""
        skip_reveal = False

        for i, word in enumerate(words):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                if event.type == pygame.KEYDOWN:
                    skip_reveal = True
            if skip_reveal:
                current_text = instruction
                break

            current_text = (current_text + " " + word).strip()
            self.screen.fill((0, 0, 0))
            text = self.font.render(current_text, True, (255, 255, 0))
            text_rect = text.get_rect(center=self.screen.get_rect().center)
            self.screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.delay(250)

        if not self.running:
            return

        if skip_reveal:
            self.screen.fill((0, 0, 0))
            text = self.font.render(current_text, True, (255, 255, 0))
            text_rect = text.get_rect(center=self.screen.get_rect().center)
            self.screen.blit(text, text_rect)
            pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                if event.type == pygame.KEYDOWN:
                    waiting = False
            self.clock.tick(60)

        while self.running:
            self._render_background()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -self.move_speed
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = self.move_speed
            if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -self.move_speed
            if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = self.move_speed
            
            self.move_with_collision(self.player_rect, dx, dy)
            self.player_rect.clamp_ip(pygame.Rect(0, 0, self.world_width, self.world_height))
            self.camera_x = max(0, min(self.player_rect.centerx - self.screen_w // 2, self.world_width - self.screen_w))

            self.spawn_timer += 1
            if self.spawn_timer > 75:
                self.spawn_raider()
                self.spawn_timer = 0

            if self.invincible_timer > 0:
                self.invincible_timer -= 1

            for r in self.raiders:
                rdx = r["speed"] if r["rect"].x < self.player_rect.x else -r["speed"]
                rdy = r["speed"] if r["rect"].y < self.player_rect.y else -r["speed"]
                
                self.move_with_collision(r["rect"], rdx, rdy)
                
                if self.invincible_timer <= 0:
                    if r["rect"].colliderect(self.player_rect):
                        return self.end_screen(True) # Captured

            cam_left = self.camera_x - 200
            cam_right = self.camera_x + self.screen_w + 200
            self.raiders = [
                r for r in self.raiders
                if cam_left <= r["rect"].x <= cam_right
                and -100 <= r["rect"].y <= self.world_height + 100
            ]

            for tree_hitbox in self.trees:
                self.screen.blit(
                    self.tree_sprite,
                    (tree_hitbox.x - self.tree_offset_x - self.camera_x, tree_hitbox.y - self.tree_offset_y)
                )
            
            self.screen.blit(self.esi_sprite, (self.player_rect.x - self.camera_x, self.player_rect.y))
            if self.invincible_timer > 0:
                pygame.draw.circle(
                    self.screen,
                    (255, 255, 255),
                    (self.player_rect.centerx - self.camera_x, self.player_rect.centery),
                    30,
                    2
                )
            
            for r in self.raiders:
                self.screen.blit(self.raider_sprite, (r["rect"].x - self.camera_x, r["rect"].y))

            if self.player_rect.x > self.world_width - 60:
                return self.end_screen(False) # Escaped

            pygame.draw.rect(self.screen, (0, 0, 0), (0, self.screen_h - 40, self.screen_w, 40))
            label = self.font.render("", True, (255, 255, 255))
            self.screen.blit(label, (250, self.screen_h - 35))

            pygame.display.flip()
            self.clock.tick(60)

    def end_screen(self, captured):
        self.screen.fill((0, 0, 0))
        msg = "CAPTURED: THE CASTLE AWAITS" if captured else "ESCAPED: THE SPIRITS PROTECT YOU"
        color = (255, 0, 0) if captured else (0, 255, 0)

        words = msg.split(" ")
        current_text = ""
        for word in words:
            current_text = (current_text + " " + word).strip()
            self.screen.fill((0, 0, 0))
            text = self.font.render(current_text, True, color)
            text_rect = text.get_rect(center=self.screen.get_rect().center)
            self.screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.delay(250)

        pygame.time.delay(2000)
        return captured

if __name__ == "__main__":
    game = EsiEscapeGame()
    game.run()
    pygame.quit()


