import json
import pygame

from src.sprite import Sprite

class AssetManager:
    NULL_IMAGE: pygame.Surface | None = None

    AUDIO_ASSETS: dict[str, pygame.mixer.Sound] = {}
    FONT_ASSETS: dict[str, pygame.font.Font] = {}
    IMAGE_ASSETS: dict[str, pygame.Surface] = {}
    SPRITES: dict[str, Sprite] = {}

    def __init__(self, asset_guide: str):
        with open(asset_guide, "r") as file:
            obj = json.load(file)

        for audio in obj.get("audio", []):
            self.add_audio(
                name=audio.get("name"),
                audio_path=audio.get("path")
            )

        for font in obj.get("fonts", []):
            for size in font.get("sizes", []):
                self.add_font(
                    name=font.get("name"),
                    font_path=font.get("path"),
                    font_size=size
                )

        for image in obj.get("images", []):
            self.add_image(
                name=image.get("name"),
                image_path=image.get("path")
            )

        for sprite in obj.get("sprites", []):
            self.add_sprite(
                name=sprite.get("name"),
                sprite_sheet=sprite.get("sprite_sheet"),
                dimensions=pygame.Vector2(sprite.get("width"), sprite.get("height")),
                animations=sprite.get("animations"),
                animation_layout=sprite.get("animation_layout"),
                num_frames=sprite.get("num_frames")
            )

    @classmethod
    def add_audio(cls, name: str, audio_path: str) -> None:
        cls.AUDIO_ASSETS[name] = pygame.mixer.Sound(audio_path)

    @classmethod
    def add_font(cls, name: str, font_path: str, font_size: int) -> None:
        cls.FONT_ASSETS[name + str(font_size)] = pygame.font.Font(font_path, font_size)

    @classmethod
    def add_image(cls, name: str, image_path: str) -> None:
        cls.IMAGE_ASSETS[name] = pygame.image.load(image_path).convert_alpha()

    @classmethod
    def add_sprite(cls, name: str, sprite_sheet: str, dimensions: pygame.Vector2,
                   animations: list[str], animation_layout: str,
                   num_frames: int) -> None:
        cls.SPRITES[name] = Sprite(
            spritesheet=AssetManager.get_image(sprite_sheet),
            dimensions=dimensions,
            animations=animations,
            row_major=animation_layout == "rows",
            num_frames=num_frames
        )

    @classmethod
    def get_audio(cls, name: str) -> pygame.mixer.Sound | None:
        return cls.AUDIO_ASSETS.get(name, None)

    @classmethod
    def get_font(cls, name: str) -> pygame.font.Font | None:
        return cls.FONT_ASSETS.get(name, None)

    @classmethod
    def get_image(cls, name: str) -> pygame.Surface | None:
        return cls.IMAGE_ASSETS.get(name, None)

    @classmethod
    def get_sprite(cls, name: str) -> Sprite | None:
        return cls.SPRITES.get(name, None)