import pygame

from src.game import Game
from src.game_backends.backend import GameState

def main():
    pygame.init()

    state: GameState = GameState.MAIN_MENU
    game: Game = Game("assets/asset_guide.json", "scenes/scene_guide.json", "config.json", game_state=state)
    game.run(60)

if __name__ == "__main__":
    main()
