import pygame
import json

from src.sprite import Sprite

class AssetManager:
    def __init__(self, asset_guide: str):
        self.audio_assets: dict[str, pygame.mixer.Sound] = {}
        self.font_assets: dict[str, pygame.font.Font] = {}
        self.image_assets: dict[str, pygame.Surface] = {}
        self.sprites: dict[str, Sprite] = {}

        with open(asset_guide, "r") as file:
            obj = json.load(file)

        for audio in obj["audio"]:
            self.add_audio(name=audio["name"], audio_path=audio["path"])

        for font in obj["fonts"]:
            for size in font["sizes"]:
                self.add_font(name=font["name"], font_path=font["path"], font_size=size)

        for image in obj["images"]:
            self.add_image(name=image["name"], image_path=image["path"])

        for sprite in obj["sprites"]:
            self.add_sprite(name=sprite["name"],
                            sprite_sheet=sprite["sprite_sheet"],
                            dimensions=pygame.Vector2(sprite["width"], sprite["height"]),
                            animations=sprite["animations"],
                            animation_layout=sprite["animation_layout"],
                            num_frames=sprite["num_frames"],
                            direction=sprite["direction"],
                            frame_time=sprite["frame_time"])

    def add_audio(self, name: str, audio_path: str) -> None:
        self.audio_assets[name] = pygame.mixer.Sound(file=audio_path)

    def add_font(self, name: str, font_path: str, font_size: int) -> None:
        self.font_assets[name + str(font_size)] = pygame.font.Font(font_path, font_size)

    def add_image(self, name: str, image_path: str) -> None:
        self.image_assets[name] = pygame.image.load(image_path)

    def add_sprite(self, name: str, sprite_sheet: str, dimensions: pygame.Vector2,
                   animations: list[str], animation_layout: str,
                   num_frames: int, direction: bool, frame_time: float) -> None:
        self.sprites[name] = Sprite(
            self.image_assets[sprite_sheet], dimensions,
            animations, animation_layout == "rows",
            num_frames, direction, frame_time
        )

    def get_audio(self, name: str) -> pygame.mixer.Sound:
        return self.audio_assets[name]

    def get_font(self, name: str) -> pygame.font.Font:
        return self.font_assets[name]

    def get_image(self, name: str) -> pygame.Surface:
        return self.image_assets[name]

    def get_sprite(self, name: str) -> Sprite:
        return self.sprites[name]