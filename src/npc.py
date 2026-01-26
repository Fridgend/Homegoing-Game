import pygame

from src.dialogue import Dialogue
from src.entity import Entity
from src.interactable import Interactable
from src.ui_manager import UIManager
from src.sprite import Sprite
from src.player import Player

class NPC(Entity, Interactable):
    def __init__(self, grid_pos: pygame.Vector2, sprite: Sprite, collision: bool, dialogue: Dialogue):
        Entity.__init__(self, grid_pos=grid_pos, sprite=sprite, collision=collision)
        Interactable.__init__(self)
        self.dialogue: Dialogue = dialogue

    def can_interact(self, player: Player):
        return self.grid_pos.distance_to(player.grid_pos + player.facing) == 0
    
    def interact(self, player: Player, ui_manager: UIManager):
        if self.block:
            return
        self.look_at(player.grid_pos)
        self.dialogue.start()
        ui_manager.set_dialogue(self.dialogue)
        self.block = True

    def input(self, keys: pygame.key.ScancodeWrapper):
        pass

    def update(self, ui_manager: UIManager, dt: float):
        self.sprite.update(dt)
        if self.block and not self.dialogue.playing:
            self.look_at(self.grid_pos + pygame.Vector2(0, 1))
            self.elapsed_time += dt
            if self.elapsed_time > 1:
                self.elapsed_time = 0
                self.block = False