import pygame
import torch
import torch.nn as nn
import math
import random

class ChaosDirector(nn.Module):
    def __init__(self):
        super().__init__()
        self.brain = nn.Linear(3, 1)

    def get_spawn_count(self, heritage, will, kills):
        with torch.no_grad():
            x = torch.tensor([heritage, will, kills/10.0], dtype=torch.float32)
            intensity = torch.sigmoid(self.brain(x)).item()
            return int(3 + (intensity * 5))

class Officer:
    def __init__(self, x, y):
        self.pos = [float(x), float(y)]
        self.hp = 50
        self.speed = random.uniform(2.0, 3.5)
        self.size = 25
        self.color = (240, 240, 240) # The "White Men"

    def update(self, target_pos):
        dist = math.hypot(target_pos[0]-self.pos[0], target_pos[1]-self.pos[1])
        if dist > 0:
            self.pos[0] += (target_pos[0]-self.pos[0])/dist * self.speed
            self.pos[1] += (target_pos[1]-self.pos[1])/dist * self.speed
        return dist

class Spear:
    def __init__(self, start, target, dmg):
        self.pos = list(start)
        angle = math.atan2(target[1]-start[1], target[0]-start[0])
        self.vel = [math.cos(angle)*15, math.sin(angle)*15]
        self.dmg = dmg

class EsiSwarmGame:
    def __init__(self, heritage=1.5, will=1.5, has_stone=True):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24, bold=True)
        
        
        self.heritage = heritage
        self.will = will
        self.has_stone = has_stone
        self.director = ChaosDirector()
        
        self.pos = [400, 300]
        self.hp = 100
        self.kills = 0
        self.spears = []
        
        self.enemies = []
        self.spawn_timer = 0
        self.running = True

    def spawn_squad(self):
        count = self.director.get_spawn_count(self.heritage, self.will, self.kills)
        
        for _ in range(count):
            edge = random.choice(['top', 'bottom', 'left', 'right'])
            if edge == 'top': x, y = random.randint(0, 800), -50
            elif edge == 'bottom': x, y = random.randint(0, 800), 650
            elif edge == 'left': x, y = -50, random.randint(0, 600)
            else: x, y = 850, random.randint(0, 600)
            
            self.enemies.append(Officer(x, y))

    def handle_input(self):
        keys = pygame.key.get_pressed()
        speed = 5
        # Movement
        if keys[pygame.K_a]: self.pos[0] -= speed
        if keys[pygame.K_d]: self.pos[0] += speed
        if keys[pygame.K_w]: self.pos[1] -= speed
        if keys[pygame.K_s]: self.pos[1] += speed

    def run(self):
        while self.running:
            self.screen.fill((60, 20, 10)) 
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.fire_spear()

            self.handle_input()

            self.spawn_timer += 1
            if self.spawn_timer > 90: # Every 1.5 seconds
                self.spawn_squad()
                self.spawn_timer = 0

            for s in self.spears[:]:
                s.pos[0] += s.vel[0]
                s.pos[1] += s.vel[1]
                if not (0 < s.pos[0] < 800 and 0 < s.pos[1] < 600):
                    self.spears.remove(s)
                    continue
                for e in self.enemies[:]:
                    if math.hypot(s.pos[0]-e.pos[0], s.pos[1]-e.pos[1]) < 20:
                        e.hp -= s.dmg
                        if s in self.spears: self.spears.remove(s)
                        if e.hp <= 0:
                            self.enemies.remove(e)
                            self.kills += 1

            for e in self.enemies:
                dist = e.update(self.pos)
                if dist < 20:
                    self.hp -= 0.5 

            target = self.get_nearest_enemy()
            if target:
                pygame.draw.line(self.screen, (255, 215, 0), self.pos, target.pos, 1)

            pygame.draw.circle(self.screen, (200, 150, 50), (int(self.pos[0]), int(self.pos[1])), 20)
            if self.has_stone: pygame.draw.circle(self.screen, (0,0,0), (int(self.pos[0]), int(self.pos[1])), 6)

            for e in self.enemies:
                pygame.draw.rect(self.screen, e.color, (int(e.pos[0]-12), int(e.pos[1]-12), 25, 25))
            
            for s in self.spears:
                pygame.draw.circle(self.screen, (255, 255, 0), (int(s.pos[0]), int(s.pos[1])), 4)

            self.draw_ui()

            if self.hp <= 0: return True 
            if self.kills >= 40: return False 

            pygame.display.flip()
            self.clock.tick(60)

    def get_nearest_enemy(self):
        if not self.enemies: return None
        return min(self.enemies, key=lambda e: math.hypot(e.pos[0]-self.pos[0], e.pos[1]-self.pos[1]))

    def fire_spear(self):
        target = self.get_nearest_enemy()
        if target:
            dmg = 20 * (self.will + (self.heritage * 0.5))
            self.spears.append(Spear(self.pos, target.pos, dmg))

    def draw_ui(self):
        pygame.draw.rect(self.screen, (100, 0, 0), (20, 560, 200, 20))
        pygame.draw.rect(self.screen, (0, 200, 0), (20, 560, self.hp * 2, 20))
        
        info = self.font.render(f"KILLS: {self.kills} / 40  |  SPIRIT: {int(self.hp)}%", True, (255, 255, 255))
        fury = self.font.render("SURVIVE THE RAID", True, (255, 0, 0))
        self.screen.blit(info, (20, 20))
        self.screen.blit(fury, (300, 20))

if __name__ == "__main__":
    game = EsiSwarmGame(heritage=1.8, will=1.5)
    result = game.run()
    pygame.quit()
    print("ESI WAS CAPTURED" if result else "ESI ESCAPED INTO THE NIGHT")