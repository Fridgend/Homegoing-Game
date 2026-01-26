import pygame
import json

class Config:
    def __init__(self, config_path: str):
        self.window_dims: pygame.Vector2 = pygame.Vector2(0, 0)
        self.window_fullscreen: bool = False
        self.dialogue_box_dims_fractions: pygame.Vector2 = pygame.Vector2(0, 0)
        self.dialogue_box_dims: pygame.Vector2 = pygame.Vector2(0, 0)
        self.dialogue_box_pos_fractions: pygame.Vector2 = pygame.Vector2(0, 0)
        self.dialogue_box_pos: pygame.Vector2 = pygame.Vector2(0, 0)
        self.tile_size: int = 32

        self.load(config_path)

    def load(self, config_path: str) -> None:
        with open(config_path, "r") as file:
            obj = json.load(file)

        if (window_dimensions := obj.get("window_dimensions", None)) is not None:
            self.window_dims = pygame.Vector2(window_dimensions)

        if (fullscreen := obj.get("window_fullscreen", None)) is not None:
            self.window_fullscreen = fullscreen

        if (dlg_box_dims := obj.get("dialogue_box_dimensions", None)) is not None:
            self.dialogue_box_dims_fractions = pygame.Vector2(dlg_box_dims)
            self.dialogue_box_dims = pygame.Vector2(round(dlg_box_dims[0] * self.window_dims.x),
                                                    round(dlg_box_dims[1] * self.window_dims.y))

        if (dlg_box_pos := obj.get("dialogue_box_position", None)) is not None:
            self.dialogue_box_pos_fractions = pygame.Vector2(dlg_box_pos)
            self.dialogue_box_dims = pygame.Vector2(round(dlg_box_pos[0] * self.window_dims.x),
                                                    round(dlg_box_pos[1] * self.window_dims.y))

        if (tile_size := obj.get("tile_size", None)) is not None:
            self.tile_size = tile_size

    def set_window_dimensions(self, dims: tuple) -> None:
        self.window_dims = pygame.Vector2(dims)

        self.dialogue_box_dims = pygame.Vector2(round(self.dialogue_box_dims_fractions.x * self.window_dims.x),
                                                round(self.dialogue_box_dims_fractions.y * self.window_dims.y))
        self.dialogue_box_dims = pygame.Vector2(round(self.dialogue_box_pos_fractions.x * self.window_dims.x),
                                                round(self.dialogue_box_pos_fractions.y * self.window_dims.y))

config: Config | None = None