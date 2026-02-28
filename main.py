import pygame
import asyncio

from src.game import Game
from src.game_backends.backend import GameState

async def main():
    print("Hello, world, from async def main() #############################")
    pygame.init()

    state: GameState = GameState.MAIN_MENU
    game: Game = Game("assets/asset_guide.json", "scenes/scene_guide.json", "config.json", game_state=state)
    await game.run(60)

asyncio.run(main())