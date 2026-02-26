from src.dialogue import Dialogue
from src.player import Player

class Interactable:
    def __init__(self):
        self.block: bool = False
        self.elapsed_time: float = 0

    def can_interact(self, player: Player) -> bool:
        return not self.block

    def interact(self, player: Player, dialogue: str | None = None) -> Dialogue | None:
        pass