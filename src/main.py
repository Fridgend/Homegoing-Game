import pygame

from src.game import Game

def main():
    pygame.font.init()
    pygame.mixer.init()

    game: Game = Game("assets/asset_guide.json")
    game.run(60)

if __name__ == "__main__":
    main()