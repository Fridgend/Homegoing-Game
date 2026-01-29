import pygame

def dir_to_str(direction: pygame.Vector2) -> str:
    match (direction.x, direction.y):
        case (0, 0) | (0, 1): return "down"
        case (1, 0): return "right"
        case (0, -1): return "up"
        case (-1, 0): return "left"

class Sprite:
    def __init__(self, spritesheet: pygame.Surface, dimensions: pygame.Vector2,
                 animations: list[str], row_major: bool,
                 num_frames: int, direction: bool, frame_time: float = 0.2):

        self.frames: dict[str, list[pygame.Surface]] = {}
        self.compound: bool = direction
        self.dimensions: pygame.Vector2 = dimensions
        self.num_frames: int = num_frames

        self.frame_progress: float = 0
        self.frame_time: float = frame_time
        self.frame_index: int = 0

        self.init_frames(spritesheet, animations, row_major)

    def init_frames(self, spritesheet: pygame.Surface, animations: list[str], row_major: bool) -> None:
        elements: int = self.num_frames
        if self.compound: elements *= len(animations)

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
        self.frame_index = 0

    def get(self, animation: str) -> pygame.Surface | None:
        if self.frames.get(animation, False):
            return self.frames[animation][self.frame_index]
        else:
            return None

    def update(self, dt: float) -> None:
        self.frame_progress += dt
        if self.frame_progress >= self.frame_time:
            self.frame_progress = 0
            self.frame_index += 1
            self.frame_index %= self.num_frames