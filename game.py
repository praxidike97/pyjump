import pygame
import numpy as np
import random
import argparse
import time
import threading

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
DARK_BLUE = (0, 0, 51)


class Game():
    def __init__(self):
        self.scrolling = False
        self.current_scrolling_steps = 0
        self.scrolling_speed = 3
        self.bars = list()
        self.running = False

        # For programming interface: the game just continues, when step is called
        self.step_wait = True

        # For programming interface: step function waits, until new state is set
        self.state_set = False

        # For programming interface: the current state of the game
        self.state = None

        # For programming interface: whether to render or not
        self.render = True

        # For programming interface: the last bar the player jumped on
        self.last_jumped_on_bar = None

        self.play = False
        self.window = None

        self.last_bar_left = False

        self.done = False

        # Create the player
        self.player = Player()

        self.margin_bottom = SCREEN_HEIGHT #SCREEN_HEIGHT - 100

        # Create initial bars
        #bar_positions = [(random.randint(30, SCREEN_WIDTH - BAR_WIDTH - 30), 400),
        #                 (random.randint(30, SCREEN_WIDTH - BAR_WIDTH - 30), 300),
        #                 (random.randint(30, SCREEN_WIDTH - BAR_WIDTH - 30), 200),
        #                 (random.randint(30, SCREEN_WIDTH - BAR_WIDTH - 30), 100),
        #                 (random.randint(30, SCREEN_WIDTH - BAR_WIDTH - 30), 500)]

        # Create initial bars
        bar_positions = [(210, 400),
                         (40, 300),
                         (210, 200),
                         (40, 100),
                         (40, 500)]

        for bar_position in bar_positions:
            self.bars.append(Bar(position=bar_position))

    def generate_new_bars(self):
        list_bars = list()
        bar = Bar(position=(random.randint(30, SCREEN_WIDTH - BAR_WIDTH - 30), -20))

        list_bars.append(bar)
        self.bars += list_bars

    def check_is_on_bar(self):
        # Check if the player will arrive on a bar in the next movement
        for bar in self.bars:
            #print("play.rect.y: %f  bar.rect.y - bar.rect.height: %f  new play.rect.y: %f" % (self.player.rect.y + self.player.rect.height / 2, bar.rect.y - bar.rect.height, self.player.rect.y + self.player.rect.height / 2 - round((self.player.initial_jumping_velocity - g * self.player.jumping_time)) + 5))
            if (bar.rect.x - bar.rect.width / 2 < self.player.rect.x - self.player.rect.width / 2 < bar.rect.x + bar.rect.width / 2 or \
                bar.rect.x - bar.rect.width / 2 < self.player.rect.x + self.player.rect.width / 2 < bar.rect.x + bar.rect.width / 2) and \
                    self.player.rect.y + self.player.rect.height / 2 < bar.rect.y - bar.rect.height < self.player.rect.y + self.player.rect.height / 2 - round((self.player.initial_jumping_velocity - g * self.player.jumping_time)) + 5:
                self.last_jumped_on_bar = bar
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
            if g * self.player.jumping_time > self.player.initial_jumping_velocity:
                if self.player.rect.y < self.margin_bottom and self.margin_bottom - self.player.rect.y > 10:
                    self.current_scrolling_steps = int((self.margin_bottom - self.player.rect.y) / self.scrolling_speed)
                    self.scrolling = True
                    self.player.score += int((self.margin_bottom - self.player.rect.y))
                    self.generate_new_bars()

                self.player.jumping_time = 0.0
        else:
            movement += np.array([0, -(self.player.initial_jumping_velocity - g * self.player.jumping_time)]).astype(
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
            self.done = True
            #quit()

        # Check if bars need to be removed
        new_bars = list()
        for bar in self.bars:
            if bar.rect.y + bar.rect.height / 2 < SCREEN_HEIGHT:
                new_bars.append(bar)
        self.bars = new_bars

        # Increase the jumping time
        self.player.jumping_time += dt

    def _start(self, play=False):
        pygame.font.init()
        step_capture = 0

        while True:

            # Discretize the game
            if not play:
                while self.step_wait:
                    pass

            self.step_wait = True

            #dt = clock.tick(FPS) / 1000
            dt = 1./60.

            if self.render and self.play:
                time.sleep(dt)

            screen.fill(DARK_BLUE)

            # Query if the player pressed a key
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    # Check if player moves to the right or to the left
                    self.player.is_moving_left = (event.key == pygame.K_a)
                    self.player.is_moving_right = (event.key == pygame.K_d)
                elif event.type == pygame.KEYUP:
                    # Stop all movements
                    self.player.is_moving_left = self.player.is_moving_right = False

            # Update the game (also updates the player and the bars)
            self.update(dt=dt)

            # Set the new state of the game (normalized state!!!)
            closest_bar = self.get_closest_bar()
            current_velocity = self.player.initial_jumping_velocity - g * self.player.jumping_time
            y_distance = (self.player.rect.y - closest_bar.rect.y)/SCREEN_HEIGHT/2.
            x_distance_left = (closest_bar.rect.x + closest_bar.rect.width/2 - self.player.rect.y) / SCREEN_WIDTH
            x_distance_right = (closest_bar.rect.x - closest_bar.rect.width/2 - self.player.rect.y) / SCREEN_WIDTH
            self.state = [self.player.rect.x/SCREEN_WIDTH, self.player.rect.y/SCREEN_HEIGHT/2., y_distance, x_distance_left, x_distance_right, current_velocity/self.player.initial_jumping_velocity]
            self.state_set = True

            if self.render:
                # Draw the new player position and bars
                screen.blit(self.player.image, self.player.rect)
                for bar in self.bars:
                    screen.blit(bar.image, bar.rect)

                # Set the score
                myfont = pygame.font.SysFont('Arial', 20)
                textsurface = myfont.render(str(self.player.score), False, (255, 255, 255))
                text_rect_obj = textsurface.get_rect()
                screen.blit(textsurface, text_rect_obj)

                #if not play:
                    #pass
                #    self.player.is_moving_left = self.player.is_moving_right = False
                # Update the whole screen
                pygame.display.update()

                #if not self.window is None:
                if step_capture%4 == 0:
                    pygame.image.save(screen, "capture/screenshot-%s.jpeg" % (str(step_capture)).zfill(4))

            #print(self.done)
            time.sleep(0.001)
            if self.done:
                break

            step_capture += 1

    def start(self, play=False):
        self.thread = threading.Thread(target=self._start,  args=(play,))
        self.thread.start()

    def moveRight(self):
        self.player.is_moving_right = True

    def moveLeft(self):
        self.player.is_moving_left = True

    def step(self):
        self.step_wait = False
        while not self.state_set:
            pass

        self.state_set = False

        self.player.is_moving_left = self.player.is_moving_right = False

        return self.state

    def get_closest_bar(self):
        # Find the closest bar to the player, i.e. the next bar above the player
        closest_bar = None

        # Solution 1: always find the bar that is currently closest to the player
        """
        # Find all the bars above the player
        bars_above = list()
        for bar in self.bars:
            if bar.rect.y < self.player.rect.y:
                bars_above.append(bar)

        if len(bars_above) == 0:
            return self.bars[0]

        closest_bar = bars_above[0]
        for bar in bars_above:
            if self.player.rect.y > bar.rect.y > closest_bar.rect.y:
                closest_bar = bar
        """

        # Solution 2: find the bar that is the closest to the last bar the player jumped on
        if self.last_jumped_on_bar is None:
            closest_bar = self.bars[0]
            for bar in self.bars:
                if bar.rect.y > closest_bar.rect.y:
                    closest_bar = bar
        else:
            closest_bar = self.bars[-1]
            while closest_bar.rect.y == self.last_jumped_on_bar.rect.y:
                closest_bar = random.choice(self.bars)

            for bar in self.bars:
                if self.last_jumped_on_bar.rect.y > bar.rect.y > closest_bar.rect.y:
                    closest_bar = bar

        return closest_bar

    def performAction(self, action):
        if action == 0:
            self.moveRight()
        elif action == 1:
            self.moveLeft()
        elif action == 2:
            pass

    def end(self):
        self.thread.join()


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        #self.image = pygame.Surface((32, 32))
        #self.image.fill(WHITE)

        astronautImg = pygame.image.load('img/astronaut.png')
        self.image = astronautImg

        self.score = 0

        self.rect = pygame.Surface((32, 70)).get_rect()#self.image.get_rect()

        # The initial position of the player
        self.rect.x = SCREEN_WIDTH/3
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

        barImg = pygame.image.load('img/bar.png')
        self.image = barImg

        self.rect = self.image.get_rect(x=position[0], y=position[1])

    def update(self, dt):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--play', action='store_true')
    FLAGS, unparsed = parser.parse_known_args()

    game = Game()
    game.play = FLAGS.play
    pygame.font.init()
    game.window = pygame.display.set_caption('PyJump')

    game.start(play=FLAGS.play)
