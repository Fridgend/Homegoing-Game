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

def load_esi_sprite():
    path = os.path.join("assets", "images", "Esi.png")
    return pygame.image.load(path).convert_alpha()

def load_attacker_sprite():
    path = os.path.join("assets", "images", "attacker_for_minigame.png")
    return pygame.image.load(path).convert_alpha()

def load_spear_sprite():
    path = os.path.join("assets", "images", "spear_Esi.png")
    return pygame.image.load(path).convert_alpha()

def draw_pixel_tree():
    s = pygame.Surface((64, 80), pygame.SRCALPHA)
    pygame.draw.rect(s, (80, 50, 20), (26, 40, 12, 40)) 
    pygame.draw.circle(s, (20, 80, 20), (32, 30), 28) 
    pygame.draw.circle(s, (10, 60, 10), (15, 35), 18)
    pygame.draw.circle(s, (10, 60, 10), (50, 35), 18)
    return s

class Spear:
    def __init__(self, start, target, half_length, base_sprite):
        self.pos = pygame.Vector2(start[0], start[1])
        angle = math.atan2(target[1]-start[1], target[0]-start[0])
        self.vel = pygame.Vector2(math.cos(angle) * 16, math.sin(angle) * 16)
        self.angle_deg = math.degrees(angle)
        self.tip_offset = pygame.Vector2(half_length, 0)
        self.sprite = pygame.transform.rotate(base_sprite, -self.angle_deg)

class EsiWarGame:
    def __init__(self, will=1.5, heritage=1.5):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.screen_w, self.screen_h = self.screen.get_size()
        font_path = os.path.join("assets", "fonts", "Snake.ttf")
        self.font = pygame.font.Font(font_path, 64)
        self.ui_font = pygame.font.Font(font_path, 44)
        self.sprite_scale = 1.25
        self.esi_scale = self.sprite_scale * 1.15
        self.attacker_scale = self.sprite_scale * 1.1
        self.spear_scale = self.sprite_scale * 0.9
        self.tree_offset_x = int(26 * self.sprite_scale)
        self.tree_offset_y = int(40 * self.sprite_scale)
        self.world_width = 12000
        self.world_height = self.screen_h
        self.camera_x = 0
        
        self.engine = EnduranceEngine()
        self.move_speed = self.engine.get_speed(will, heritage) * 1.3 
        
        self.esi_sprite = self._scale_sprite(load_esi_sprite(), self.esi_scale)
        self.raider_sprite = self._scale_sprite(load_attacker_sprite(), self.attacker_scale)
        self.spear_sprite = self._scale_sprite(load_spear_sprite(), self.spear_scale)
        self.tree_sprite = self._scale_sprite(draw_pixel_tree())
        self.background_surface = self._build_background()
        
        self.player_rect = pygame.Rect(
            50, 280,
            int(22 * self.sprite_scale),
            int(26 * self.sprite_scale)
        )
        
        self.trees = []
        for _ in range(150):
            tx = random.randint(150, self.world_width - 100)
            ty = random.randint(50, self.world_height - 100)
            self.trees.append(pygame.Rect(
                tx + self.tree_offset_x,
                ty + self.tree_offset_y,
                int(12 * self.sprite_scale),
                int(30 * self.sprite_scale)
            ))

        self.raiders = []
        self.spears = []
        self.spear_ammo = 30
        self.spawn_timer = 0
        self.spawn_interval = 25
        self.raider_speed_min = 4.7
        self.raider_speed_max = 5.9
        self.invincible_timer = 180 # 3 seconds of grace at 60fps        
        self.running = True

    def _scale_sprite(self, surface, scale=None):
        scale = self.sprite_scale if scale is None else scale
        width = int(surface.get_width() * scale)
        height = int(surface.get_height() * scale)
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
        rect = pygame.Rect(
            x, y,
            int(24 * self.sprite_scale),
            int(28 * self.sprite_scale)
        )
        self.raiders.append({
            "rect": rect,
            "pos": pygame.Vector2(rect.centerx, rect.centery),
            "speed": random.uniform(self.raider_speed_min, self.raider_speed_max)
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

    def get_nearest_raider(self):
        if not self.raiders:
            return None
        return min(self.raiders, key=lambda r: math.hypot(
            r["rect"].centerx - self.player_rect.centerx,
            r["rect"].centery - self.player_rect.centery
        ))

    def fire_spear(self):
        target = self.get_nearest_raider()
        if target and self.spear_ammo > 0:
            start = (self.player_rect.centerx, self.player_rect.centery)
            end = (target["rect"].centerx, target["rect"].centery)
            self.spears.append(Spear(start, end, self.spear_sprite.get_width() * 0.5, self.spear_sprite))
            self.spear_ammo -= 1

    def run(self):
        self.screen.fill((0, 0, 0))
        instruction = "Get to the other side using arrows or WASD and SPACE for spears!"
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

        pygame.time.delay(3000)

        max_tries = 2
        attempts = 0
        while self.running and attempts < max_tries:
            if not self._choose_difficulty():
                return
            self._reset_round_state()
            captured = self._play_round()
            if captured is None:
                return
            if captured:
                if attempts == 0:
                    self.end_screen(True)
                    attempts += 1
                    continue
                self.end_screen(True)
                self._final_epilogue()
                return True
            self.end_screen(False)
            self._final_epilogue()
            return False

    def _choose_difficulty(self):
        waiting = True
        choosing = True
        choice_text = self.ui_font.render(
            "Choose difficulty: 1= (Easy) , 2= (Normal) , 3= (Unlikley legend)",
            True,
            (255, 255, 255)
        )
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_1, pygame.K_KP1):
                        self.spawn_interval = 45
                        self.raider_speed_min = 3.1
                        self.raider_speed_max = 4.1
                        choosing = False
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        self.spawn_interval = 30
                        self.raider_speed_min = 3.9
                        self.raider_speed_max = 4.9
                        choosing = False
                    elif event.key in (pygame.K_3, pygame.K_KP3):
                        self.spawn_interval = 22
                        self.raider_speed_min = 4.3
                        self.raider_speed_max = 5.3
                        choosing = False
                    if not choosing:
                        waiting = False 
            if choosing:
                self.screen.fill((0, 0, 0))
                self.screen.blit(choice_text, (self.screen_w // 2 - choice_text.get_width() // 2, self.screen_h // 2))
                pygame.display.flip()
            self.clock.tick(60)
        return True

    def _reset_round_state(self):
        self.player_rect.x = 50
        self.player_rect.y = 280
        self.camera_x = 0
        self.raiders = []
        self.spears = []
        self.spear_ammo = 30
        self.spawn_timer = 0
        self.invincible_timer = 180 # 3 seconds of grace at 60fps        

    def _play_round(self):
        while self.running:
            self._render_background()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.fire_spear()

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
            if self.spawn_timer > self.spawn_interval:
                self.spawn_raider()
                self.spawn_timer = 0

            if self.invincible_timer > 0:
                self.invincible_timer -= 1

            for s in self.spears[:]:
                s.pos += s.vel
                if not (0 <= s.pos.x <= self.world_width and 0 <= s.pos.y <= self.world_height):
                    self.spears.remove(s)
                    continue
                tip = s.pos + s.tip_offset.rotate(s.angle_deg)
                for r in self.raiders[:]:
                    if math.hypot(tip.x - r["rect"].centerx, tip.y - r["rect"].centery) < 18:
                        self.raiders.remove(r)
                        if s in self.spears:
                            self.spears.remove(s)
                        break

            for r in self.raiders:
                dx = self.player_rect.centerx - r["pos"].x
                dy = self.player_rect.centery - r["pos"].y
                dist = math.hypot(dx, dy)
                if dist != 0:
                    rdx = r["speed"] * dx / dist
                    rdy = r["speed"] * dy / dist
                    self.move_with_collision(r["rect"], rdx, rdy)
                    r["pos"].update(r["rect"].centerx, r["rect"].centery)
                
                if self.invincible_timer <= 0:
                    if r["rect"].colliderect(self.player_rect):
                        return True # Captured

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
            
            for r in self.raiders:
                self.screen.blit(self.raider_sprite, (r["rect"].x - self.camera_x, r["rect"].y))

            for s in self.spears:
                rect = s.sprite.get_rect(center=(int(s.pos.x - self.camera_x), int(s.pos.y)))
                self.screen.blit(s.sprite, rect.topleft)

            if self.player_rect.x > self.world_width - 60:
                return False # Escaped

            pygame.draw.rect(self.screen, (0, 0, 0), (0, self.screen_h - 40, self.screen_w, 40))
            ammo_label = self.ui_font.render(f"SPEARS: {self.spear_ammo}", True, (255, 255, 255))
            self.screen.blit(ammo_label, (20, 20))

            pygame.display.flip()
            self.clock.tick(60)
        return None

    def end_screen(self, captured):
        self.screen.fill((0, 0, 0))
        msg = "CAPTURED: You were caught in the escape!" if captured else "ESCAPED: You escaped your fate!"
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

    def _final_epilogue(self):
        self.screen.fill((0, 0, 0))
        msg = "What happens next is larger than any one life...."
        words = msg.split(" ")
        current_text = ""
        for word in words:
            current_text = (current_text + " " + word).strip()
            self.screen.fill((0, 0, 0))
            text = self.font.render(current_text, True, (255, 255, 255))
            text_rect = text.get_rect(center=self.screen.get_rect().center)
            self.screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.delay(250)
        pygame.time.delay(2000)
        self._thanks_for_playing()

    def _thanks_for_playing(self):
        self.screen.fill((0, 0, 0))
        msg = "Thanks for Playing."
        words = msg.split(" ")
        current_text = ""
        for word in words:
            current_text = (current_text + " " + word).strip()
            self.screen.fill((0, 0, 0))
            text = self.font.render(current_text, True, (255, 255, 255))
            text_rect = text.get_rect(center=self.screen.get_rect().center)
            self.screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.delay(250)
        pygame.time.delay(2000)

if __name__ == "__main__":
    game = EsiWarGame()
    game.run()
    pygame.quit()
