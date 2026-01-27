import pygame
import json

from src.sprite import Sprite


def _raise_error(module: str, field: str) -> None:
    pygame.quit()
    msg: str = "Failed to create " + module + " asset: Missing field '" + field + "'"
    raise RuntimeError(msg)

def _check_for(variables: list[str], check_map: dict, module: str) -> None:
    for variable in variables:
        if check_map.get(variable, None) is None: _raise_error(module, variable)


class AssetManager:
    def __init__(self, asset_guide: str):
        self.audio_assets: dict[str, pygame.mixer.Sound] = {}
        self.font_assets: dict[str, pygame.font.Font] = {}
        self.image_assets: dict[str, pygame.Surface] = {}
        self.sprites: dict[str, Sprite] = {}

        with open(asset_guide, "r") as file:
            obj = json.load(file)

        if obj.get("audio", None) is None: raise RuntimeError("'audio' assets not found in asset guide")
        for audio in obj["audio"]:
            _check_for(["name", "path"], audio, "audio")
            self.add_audio(name=audio["name"], audio_path=audio["path"])

        if obj.get("fonts", None) is None: raise RuntimeError("'fonts' assets not found in asset guide")
        for font in obj["fonts"]:
            _check_for(["sizes", "name", "path"], font, "font")
            for size in font["sizes"]:
                self.add_font(name=font["name"], font_path=font["path"], font_size=size)

        if obj.get("images", None) is None: raise RuntimeError("'images' assets not found in asset guide")
        for image in obj["images"]:
            _check_for(["name", "path"], image, "image")
            self.add_image(name=image["name"], image_path=image["path"])

        if obj.get("sprites", None) is None: raise RuntimeError("'sprites' assets not found in asset guide")
        for sprite in obj["sprites"]:
            _check_for(["name", "sprite_sheet", "width", "height",
                        "animations", "animation_layout", "num_frames", "direction", "frame_time"], sprite, "sprite")
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