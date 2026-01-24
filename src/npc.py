import pygame

from src.dialogue import Dialogue
from src.entity import Entity
from src.interactable import Interactable
from src.ui_manager import UIManager
from src.sprite import Sprite

class NPC(Entity, Interactable):
    def __init__(self, grid_pos: pygame.Vector2, sprite: Sprite, dialogue: Dialogue):
        Entity.__init__(self, grid_pos=grid_pos, sprite=sprite, collision=True)
        Interactable.__init__(self)
        self.dialogue: Dialogue = dialogue

    def can_interact(self, player):
        return self.grid_pos.distance_to(player.grid_pos + player.facing) == 0
    
    def interact(self, ui_manager):
        if self.block: return
        self.dialogue.start()
        ui_manager.set_dialogue(self.dialogue)
        self.block = True

    def input(self, keys: pygame.key.ScancodeWrapper):
        pass

    def update(self, ui_manager: UIManager, dt: float):
        if self.block and not ui_manager.is_in_dialogue():
            self.elapsed_time += dt
            if self.elapsed_time > 1:
                self.elapsed_time = 0
                self.block = False