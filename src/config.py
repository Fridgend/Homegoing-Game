import pygame
import json

class Config:
    WINDOW_DIMS: pygame.Vector2 = pygame.Vector2(0, 0)
    WINDOW_FULLSCREEN: bool = False
    TILE_SIZE: int = 32

    DIALOGUE_BOX_DIMS_FRACTIONS: pygame.Vector2 = pygame.Vector2(0, 0)
    DIALOGUE_BOX_DIMS: pygame.Vector2 = pygame.Vector2(0, 0)
    DIALOGUE_BOX_POS_FRACTIONS: pygame.Vector2 = pygame.Vector2(0, 0)
    DIALOGUE_BOX_POS: pygame.Vector2 = pygame.Vector2(0, 0)
    DIALOGUE_BOX_BACKGROUND_COLOR: pygame.Vector3 = pygame.Vector3(0, 0, 0)
    DIALOGUE_BOX_OUTLINE_COLOR: pygame.Vector3 = pygame.Vector3(0, 0, 0)
    DIALOGUE_BOX_OUTLINE_THICKNESS: int = 3
    DIALOGUE_TRIANGLE_COLOR: pygame.Vector3 = pygame.Vector3(0, 0, 0)

    @classmethod
    def load(cls, config_path: str) -> None:
        with open(config_path, "r") as file:
            obj = json.load(file)

        if (window_dimensions := obj.get("window_dimensions", None)) is not None:
            cls.WINDOW_DIMS = pygame.Vector2(window_dimensions)

        if (fullscreen := obj.get("window_fullscreen", None)) is not None:
            cls.WINDOW_FULLSCREEN = fullscreen

        if (dlg_box_dims := obj.get("dialogue_box_dimensions", None)) is not None:
            cls.DIALOGUE_BOX_DIMS_FRACTIONS = pygame.Vector2(dlg_box_dims)
            cls.DIALOGUE_BOX_DIMS = pygame.Vector2(round(dlg_box_dims[0] * cls.WINDOW_DIMS.x),
                                                   round(dlg_box_dims[1] * cls.WINDOW_DIMS.y))

        if (dlg_box_pos := obj.get("dialogue_box_position", None)) is not None:
            cls.DIALOGUE_BOX_POS_FRACTIONS = pygame.Vector2(dlg_box_pos)
            cls.DIALOGUE_BOX_POS = pygame.Vector2(round(dlg_box_pos[0] * cls.WINDOW_DIMS.x),
                                                  round(dlg_box_pos[1] * cls.WINDOW_DIMS.y))

        if (tile_size := obj.get("tile_size", None)) is not None:
            cls.TILE_SIZE = tile_size

        if (dlg_box_bg_color := obj.get("dialogue_box_background", None)) is not None:
            cls.DIALOGUE_BOX_BACKGROUND_COLOR = pygame.Vector3(dlg_box_bg_color)

        if (dlg_box_outline_color := obj.get("dialogue_box_outline", None)) is not None:
            cls.DIALOGUE_BOX_OUTLINE_COLOR = pygame.Vector3(dlg_box_outline_color)

        if (dlg_box_outline_thickness := obj.get("dialogue_box_outline_thickness", None)) is not None:
            cls.DIALOGUE_BOX_OUTLINE_THICKNESS = dlg_box_outline_thickness

        if (tri_color := obj.get("triangle_color", None)) is not None:
            cls.DIALOGUE_TRIANGLE_COLOR = pygame.Vector3(tri_color)

    @classmethod
    def set_window_dimensions(cls, dims: tuple) -> None:
        cls.WINDOW_DIMS = pygame.Vector2(dims)

        cls.DIALOGUE_BOX_DIMS = pygame.Vector2(round(cls.DIALOGUE_BOX_DIMS_FRACTIONS.x * cls.WINDOW_DIMS.x),
                                               round(cls.DIALOGUE_BOX_DIMS_FRACTIONS.y * cls.WINDOW_DIMS.y))
        cls.DIALOGUE_BOX_POS = pygame.Vector2(round(cls.DIALOGUE_BOX_POS_FRACTIONS.x * cls.WINDOW_DIMS.x),
                                              round(cls.DIALOGUE_BOX_POS_FRACTIONS.y * cls.WINDOW_DIMS.y))