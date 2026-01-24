import pygame

from src.scenes.scene import Scene
from src.player import Player
from src.asset_manager import AssetManager
from src.ui_manager import UIManager
from src.camera import Camera
from src.npc import NPC
from src.dialogue import Dialogue, Monologue
from src.interactable import Interactable

class TestScene(Scene):
    def __init__(self):
        super().__init__()
        self.bounds = pygame.Vector2(3000, 3000)

    def load(self, asset_manager: AssetManager):
        self.player = Player(pygame.Vector2(0, 0), asset_manager.get_sprite("player"), 0.15)
        self.player.grid_pos = (self.bounds // self.player.sprite.dimensions.x) // 2
        self.player.pos = self.player.grid_pos * self.player.sprite.dimensions.x

        monologue1 = Monologue("strangely familiar stranger", ["do i know you? ", "you look familiar"], [0.05, 0.05], asset_manager.get_font("snake64"))
        monologue2 = Monologue("you", ["what"], [0.25], asset_manager.get_font("snake64"), speaker_image=asset_manager.get_image("null"))
        monologue3 = Monologue("strangely familiar stranger", ["okay bye now"], [0.05], asset_manager.get_font("snake64"))
        monologue4 = Monologue("you", ["okay bye"], [0.05], asset_manager.get_font("snake64"), speaker_image=asset_manager.get_image("null"))
        monologue1.set_next_monologue(monologue2)
        monologue2.set_next_monologue(monologue3)
        monologue3.set_next_monologue(monologue4)

        npc = NPC(pygame.Vector2(1564 // 32, 1564 // 32), asset_manager.get_sprite("player"), Dialogue(monologue1))
        self.entities.append(npc)

    def input(self, ui_manager: UIManager, keys: pygame.key.ScancodeWrapper):
        if ui_manager.is_in_dialogue():
            ui_manager.input(keys)
            return

        self.player.input(keys)

        if not (keys[pygame.K_SPACE] or keys[pygame.K_RETURN]): return
        for entity in self.entities:
            entity.input(keys)
            if isinstance(entity, Interactable) and entity.can_interact(self.player):
                entity.interact(self.player, ui_manager)

    def update(self, camera: Camera, ui_manager: UIManager, dt: float):
        camera.center(self.player.pos, self.bounds)

        self.player.update(self.entities, ui_manager, dt)
        self.player.pos.x = max(0, min(self.player.pos.x, self.bounds.x - self.player.sprite.dimensions.x))
        self.player.pos.y = max(0, min(self.player.pos.y, self.bounds.y - self.player.sprite.dimensions.y))

        ui_manager.update(dt)

        for entity in self.entities: entity.update(ui_manager, dt)

    def render(self, window_surface: pygame.Surface, camera: Camera):
        window_surface.fill((70, 120, 70))

        for x in range(16, int(self.bounds.x) + 32, 32):
            pygame.draw.line(
                window_surface, (90, 140, 90), 
                camera.world_pos_to_view_pos(pygame.Vector2(x, 0)),
                camera.world_pos_to_view_pos(pygame.Vector2(x, self.bounds.y))
            )
        for y in range(16, int(self.bounds.y) + 32, 32):
            pygame.draw.line(
                window_surface, (90, 140, 90), 
                camera.world_pos_to_view_pos(pygame.Vector2(0, y)),
                camera.world_pos_to_view_pos(pygame.Vector2(self.bounds.x, y))
            )

        for entity in self.entities: entity.render(window_surface, camera)
        self.player.render(window_surface, camera)