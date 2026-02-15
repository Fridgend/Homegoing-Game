import pygame

def dir_to_str(moving: pygame.Vector2, facing: pygame.Vector2) -> str | None:
    if moving.x != 0 or moving.y != 0:
        match (moving.x, moving.y):
            case (0, 1):
                return "move_down"
            case (1, 0):
                return "move_down"
            case (0, -1):
                return "move_down"
            case (-1, 0):
                return "move_down"
            case _:
                return None

    match (facing.x, facing.y):
        case (0, 1):
            return "idle_down"
        case (1, 0):
            return "idle_down"
        case (0, -1):
            return "idle_down"
        case (-1, 0):
            return "idle_down"
        case _:
            return None

DEFAULT_ANIM: str = "idle_down"
DEFAULT_FRAME_TIME: float = 0.2

class Sprite:
    def __init__(self, spritesheet: pygame.Surface | None, dimensions: pygame.Vector2,
                 animations: list[str] | None, row_major: bool | None,
                 num_frames: int,

                 frames: dict[str, list[pygame.Surface]] | None = None,
                 default_anim: str | None = None,
                 frame_time: float | None = None):

        self.frames: dict[str, list[pygame.Surface]] = {}
        self.dimensions: pygame.Vector2 = dimensions
        self.num_frames: int = num_frames

        self.default_anim: str = DEFAULT_ANIM
        self.animation: str = self.default_anim

        self.frame_progress: float = 0
        self.frame_time: float = DEFAULT_FRAME_TIME
        self.frame_index: int = 0

        if frames is not None:
            for k, v in frames.items():
                self.frames[k] = []
                for frame in v:
                    self.frames[k].append(frame.copy())
            self.default_anim = default_anim
            self.frame_time = frame_time
            return

        self.init_frames(spritesheet, animations, row_major)

    def set_default_anim(self, anim: str):
        self.default_anim = anim

    def set_frame_time(self, frame_time: float):
        self.frame_time = frame_time

    def init_frames(self, spritesheet: pygame.Surface, animations: list[str], row_major: bool) -> None:
        elements: int = self.num_frames * len(animations)

        x: int = 0
        y: int = 0
        for i in range(elements):
            subsurface: pygame.Surface = spritesheet.subsurface(pygame.Rect(
                x * self.dimensions.x, y * self.dimensions.y,
                self.dimensions.x, self.dimensions.y)
            )

            animation: str = animations[y if row_major else x]
            if self.frames.get(animation, False):
                self.frames[animation].append(subsurface)
            else:
                self.frames[animation] = [subsurface]

            if row_major:
                x += 1
            else:
                y += 1

            if i % self.num_frames == self.num_frames - 1:
                if row_major:
                    x = 0
                    y += 1
                else:
                    x += 1
                    y = 0

    def reset_frames(self) -> None:
        self.frame_progress = 0
        self.frame_index = 0

    def set(self, animation: str) -> None:
        if self.animation != animation:
            self.reset_frames()
        self.animation = animation if self.frames.get(animation, False) else self.default_anim

    def get(self) -> pygame.Surface | None:
        if self.frames.get(self.animation) is None:
            return None
        return self.frames.get(self.animation)[self.frame_index]

    def update(self, dt: float) -> None:
        self.frame_progress += dt
        if self.frame_progress >= self.frame_time:
            self.frame_progress = 0
            self.frame_index += 1
            self.frame_index %= self.num_frames

def copy_sprite(sprite: Sprite) -> Sprite:
    new_sprite: Sprite = Sprite(
        spritesheet=None,
        dimensions=sprite.dimensions,
        animations=None,
        row_major=None,
        num_frames=sprite.num_frames,
        frames=sprite.frames,
        default_anim=sprite.default_anim,
        frame_time=sprite.frame_time
    )
    return new_sprite