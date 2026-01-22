import pygame
import sys

pygame.init()

# --- Fullscreen Setup ---
SCREEN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = SCREEN.get_size()
pygame.display.set_caption("Scrolling World")
CLOCK = pygame.time.Clock()
FPS = 60

# --- Colors ---
BLUE = (60, 140, 255)
GREEN = (90, 140, 90)
DARK_GREEN = (70, 120, 70)

# --- World Settings ---
WORLD_WIDTH = 3000
WORLD_HEIGHT = 3000
PLAYER_SPEED = 5
PLAYER_SIZE = 32


class Player:
    def __init__(self):
        self.x = WORLD_WIDTH // 2
        self.y = WORLD_HEIGHT // 2
        self.rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)

    def move(self, keys):
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.y -= PLAYER_SPEED
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.y += PLAYER_SPEED
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.x -= PLAYER_SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.x += PLAYER_SPEED

        # Keep player inside world bounds
        self.x = max(0, min(self.x, WORLD_WIDTH - PLAYER_SIZE))
        self.y = max(0, min(self.y, WORLD_HEIGHT - PLAYER_SIZE))

def main():
    player = Player()

    while True:
        # 1. Handle Events (Crucial to prevent OS from closing the app)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # 2. Movement
        keys = pygame.key.get_pressed()
        player.move(keys)

        # 3. Camera Logic
        # Center camera on player
        camera_x = player.x - WIDTH // 2
        camera_y = player.y - HEIGHT // 2

        # Clamp camera so it doesn't show black bars outside the world
        camera_x = max(0, min(camera_x, WORLD_WIDTH - WIDTH))
        camera_y = max(0, min(camera_y, WORLD_HEIGHT - HEIGHT))

        # 4. Drawing
        SCREEN.fill(DARK_GREEN)

        # Draw Grid (Relative to camera)
        for x in range(0, WORLD_WIDTH + 100, 100):
            pygame.draw.line(SCREEN, GREEN, (x - camera_x, 0 - camera_y), (x - camera_x, WORLD_HEIGHT - camera_y))
        for y in range(0, WORLD_HEIGHT + 100, 100):
            pygame.draw.line(SCREEN, GREEN, (0 - camera_x, y - camera_y), (WORLD_WIDTH - camera_x, y - camera_y))

        # Draw Player (Relative to camera)
        # Instead of forcing center, we draw the player based on world pos minus camera pos
        player_screen_x = player.x - camera_x
        player_screen_y = player.y - camera_y
        pygame.draw.rect(SCREEN, BLUE, (player_screen_x, player_screen_y, PLAYER_SIZE, PLAYER_SIZE))

        pygame.display.flip()
        CLOCK.tick(FPS) # Limits loop speed to 60 FPS

if __name__ == "__main__":
    main()
