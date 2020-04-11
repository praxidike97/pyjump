import pygame
import numpy as np
import random

successes, failures = pygame.init()

SCREEN_WIDTH = 320
SCREEN_HEIGHT = 560
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
FPS = 60
g = 15.
SIDEWISE_SPEED = 200.
SCROLLING_STEPS = 20
BAR_WIDTH = 50
BAR_HEIGHT = 8

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


class Game():
    def __init__(self):
        self.scrolling = False
        self.current_scrolling_steps = 0
        self.scrolling_speed = 3
        self.score = 0
        self.bars = list()
        self.jumping_time = 0.0

        # Create the player
        self.player = Player()

        self.margin_bottom = self.player.rect.y - 100

        # Create initial bars
        bar_positions = [(100, 400), (140, 300), (100, 420), (70, 200), (160, 100), (100, 500)]
        for bar_position in bar_positions:
            self.bars.append(Bar(position=bar_position))

    def generate_new_bars(self):
        list_bars = list()
        bar = Bar(position=(random.randint(30, SCREEN_WIDTH - BAR_WIDTH - 30), -20))

        list_bars.append(bar)
        self.bars += list_bars

    def check_is_on_bar(self):
        # Check if the player will arrive on a abar in the next movement
        for bar in self.bars:
            if (bar.rect.x - bar.rect.width / 2 < self.player.rect.x - self.player.rect.width / 2 < bar.rect.x + bar.rect.width / 2 or \
                bar.rect.x - bar.rect.width / 2 < self.player.rect.x + self.player.rect.width / 2 < bar.rect.x + bar.rect.width / 2) and \
                    self.player.rect.y + self.player.rect.height / 2 < bar.rect.y - bar.rect.height < self.player.rect.y + self.player.rect.height / 2 - round((self.player.initial_jumping_velocity - g * self.jumping_time)):
                return True
        return False

    def update(self, dt):
        # Update the bars
        for bar in self.bars:
            bar.update(dt=dt)

        # Update the player
        self.player.update(dt=dt)

        movement = np.array([0, 0])

        if self.check_is_on_bar():
            # Jumping time cannot be set to 0.0 if we are currently jumping up
            if g * self.jumping_time > self.player.initial_jumping_velocity:
                if self.player.rect.y < game.margin_bottom and game.margin_bottom - self.player.rect.y > 10:
                    self.current_scrolling_steps = int((game.margin_bottom - self.player.rect.y) / self.scrolling_speed)
                    self.scrolling = True
                    self.score += int((self.margin_bottom - self.player.rect.y))
                    self.generate_new_bars()

                self.jumping_time = 0.0
        else:
            movement += np.array([0, -(self.player.initial_jumping_velocity - g * self.jumping_time)]).astype(
                int)

        # Scroll the game if neccesary
        if self.scrolling:
            if self.current_scrolling_steps > 0:
                for bar in self.bars:
                    bar.rect.move_ip(np.array([0, self.scrolling_speed]))

                # player.platform.move_ip(np.array([0, game.scrolling_speed]))
                movement += np.array([0, self.scrolling_speed])
                self.current_scrolling_steps -= 1
            else:
                self.scrolling = False
                self.current_scrolling_steps = SCROLLING_STEPS

        # Apply the changes to the player:
        # 1. Jumping movement
        # 2. Scrolling, if required
        self.player.rect.move_ip(movement)

        # Check if game ends
        if self.player.rect.y + self.player.rect.height / 2 > SCREEN_HEIGHT:
            quit()

        # Check if bars need to be removed
        new_bars = list()
        for bar in self.bars:
            if bar.rect.y + bar.rect.height / 2 < SCREEN_HEIGHT:
                new_bars.append(bar)
        self.bars = new_bars

        # Increase the jumping time
        self.jumping_time += dt


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((32, 32))
        self.image.fill(WHITE)

        self.rect = self.image.get_rect()

        # The initial position of the player
        self.rect.x = 0
        self.rect.y = SCREEN_HEIGHT - self.rect.height / 2 - 1

        self.jumping_time = 0.0
        self.initial_jumping_velocity = 10.0

        self.is_moving_right = False
        self.is_moving_left = False

    def update(self, dt):
        movement = np.array([0, 0])

        if self.is_moving_left:
            # Just move to the left, if there is still space
            if self.rect.x + np.round(-SIDEWISE_SPEED * dt) >= 0:
                movement = np.round((np.array([-SIDEWISE_SPEED * dt, 0])))

        if self.is_moving_right:
            # Just move to the right, if there is still space
            if self.rect.x + self.rect.width + np.round(SIDEWISE_SPEED * dt) <= SCREEN_WIDTH:
                movement = np.round((np.array([SIDEWISE_SPEED * dt, 0])))

        self.rect.move_ip(movement)


class Bar(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__()
        self.image = pygame.Surface((BAR_WIDTH, BAR_HEIGHT))
        # Give the bar a random color
        self.image.fill((random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)))
        self.rect = self.image.get_rect(x=position[0], y=position[1])

    def update(self, dt):
        pass


if __name__ == "__main__":
    game = Game()
    pygame.font.init()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        screen.fill(BLACK)

        # Query if the player pressed a key
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                # Check if player moves to the right or to the left
                game.player.is_moving_left = (event.key == pygame.K_a)
                game.player.is_moving_right = (event.key == pygame.K_d)
            elif event.type == pygame.KEYUP:
                # Stop all movements
                game.player.is_moving_left = game.player.is_moving_right = False

        # Update the game (also updates the player and the bars)
        game.update(dt=dt)

        # Draw the new player position and bars
        screen.blit(game.player.image, game.player.rect)
        for bar in game.bars:
            screen.blit(bar.image, bar.rect)

        # Set the score
        myfont = pygame.font.SysFont('Arial', 20)
        textsurface = myfont.render(str(game.score), False, (255, 255, 255))
        text_rect_obj = textsurface.get_rect()
        screen.blit(textsurface, text_rect_obj)

        # Update the whole screen
        pygame.display.update()
