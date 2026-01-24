import pygame
import argparse

from src.game import Game, GameState
def main():
    pygame.font.init()
    pygame.mixer.init()

    parser = argparse.ArgumentParser()
    parser.add_argument("-sb", action="store_true", dest="scene_editor", default=False)
    parser.add_argument("-ec", action="store_true", dest="entity_configurer", default=False)
    res = parser.parse_args()

    if res.scene_editor and res.entity_configurer:
        print("Can not start in both Scene Editor and Entity Configurer")
        exit(1)

    state: GameState = GameState.SCENE_BUILDER if res.scene_editor else \
                       GameState.ENTITY_CONFIGURER if res.entity_configurer else \
                       GameState.MAIN_MENU

    game: Game = Game("assets/asset_guide.json", game_state=state)
    game.run(60, 50)

if __name__ == "__main__":
    main()