from src.player import Player
from src.ui_manager import UIManager

class Interactable:
    def __init__(self):
        self.block: bool = False
        self.elapsed_time: float = 0

    def can_interact(self, player: Player) -> bool:
        return self.block

    def interact(self, player: Player, ui_manager: UIManager):
        pass