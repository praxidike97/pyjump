import pygame
import numpy as np
import random

successes, failures = pygame.init()
print("Initializing pygame: {0} successes and {1} failures.".format(successes, failures))

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
RED = (255, 0, 0)


def generate_new_bars():
    list_bars = list()
    #bar01 = Bar(position=(random.randint(0, SCREEN_WIDTH-BAR_WIDTH), -70))
    bar02 = Bar(position=(random.randint(0, SCREEN_WIDTH - BAR_WIDTH), -20))

    #list_bars.append(bar01)
    list_bars.append(bar02)
    return list_bars


class Game():
    def __init__(self, margin_bottom):
        self.scrolling = False
        self.margin_bottom = margin_bottom
        self.current_scrolling_steps = 0
        self.scrolling_speed = 3
        self.score = 0
        self.bars = list()


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        IMAGE = pygame.image.load('yuying.png').convert_alpha()
        self.image = pygame.Surface((32, 32))
        self.image.fill(WHITE)

        #dself.image = IMAGE

        #self.platform_image = pygame.Surface((SCREEN_WIDTH, 32))
        #self.platform_image.fill(WHITE)
        #self.platform = self.platform_image.get_rect(x=0, y=SCREEN_HEIGHT - self.image.get_rect().height)

        #self.rect = self.image.get_rect(x=0, y=SCREEN_HEIGHT - self.image.get_rect().width - self.platform.height)
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = SCREEN_HEIGHT - self.rect.height/2 - 1

        self.velocity = np.array([0.0, 0.0])

        self.is_jumping = True
        self.jumping_time = 0.0
        self.initial_jumping_velocity = 10.0

        self.is_moving_right = False
        self.is_moving_left = False

    def check_is_on_bar(self, list_bars):
        for bar in list_bars:
            if (bar.rect.x - bar.rect.width/2 < self.rect.x-self.rect.width/2 < bar.rect.x + bar.rect.width/2 or \
                    bar.rect.x - bar.rect.width / 2 < self.rect.x + self.rect.width/2 < bar.rect.x + bar.rect.width / 2) and \
                    self.rect.y + self.rect.height/2 < bar.rect.y - bar.rect.height and self.rect.y + self.rect.height/2 - round((self.initial_jumping_velocity - g*self.jumping_time)) > bar.rect.y - bar.rect.height:
                return True
        return False

    def update(self, dt, list_bars, game):
        movement = np.array([0, 0])

        if self.is_moving_left:
            if self.rect.x + np.round(-SIDEWISE_SPEED*dt) >= 0:
                movement = np.round((np.array([-SIDEWISE_SPEED*dt, 0])))

        if self.is_moving_right:
            if self.rect.x + self.rect.width + np.round(SIDEWISE_SPEED * dt) <= SCREEN_WIDTH:
                movement = np.round((np.array([SIDEWISE_SPEED*dt, 0])))

        self.jumping_time += dt
        #if self.rect.topleft[1] - round((self.initial_jumping_velocity - g*self.jumping_time)) >= SCREEN_HEIGHT - player.platform.height - player.rect.height/2 or \
        #        self.check_is_on_bar(list_bars=list_bars):

        if self.check_is_on_bar(list_bars=list_bars):
            # Jumping time cannot be set to 0.0 if we are currently jumping up
            if g*self.jumping_time > self.initial_jumping_velocity:
                #print("Boing!")
                #print(self.rect.y)
                if self.rect.y < game.margin_bottom and game.margin_bottom - self.rect.y > 10:
                    game.current_scrolling_steps = int((game.margin_bottom - self.rect.y)/game.scrolling_speed)
                    #game.margin_bottom = self.rect.y
                    game.scrolling = True
                    print(game.current_scrolling_steps)
                    game.score += int((game.margin_bottom - self.rect.y))
                    game.bars += generate_new_bars()

                self.jumping_time = 0.0
        else:
            movement += np.array([0, -(self.initial_jumping_velocity - g*self.jumping_time)]).astype(int)

        # Scroll the game if neccesary
        if game.scrolling:
            if game.current_scrolling_steps > 0:
                for bar in list_bars:
                    bar.rect.move_ip(np.array([0, game.scrolling_speed]))

                #player.platform.move_ip(np.array([0, game.scrolling_speed]))
                movement += np.array([0, game.scrolling_speed])
                game.current_scrolling_steps -= 1
            else:
                game.scrolling = False
                game.current_scrolling_steps = SCROLLING_STEPS

        # CHeck if game ends
        if self.rect.y + self.rect.height/2 > SCREEN_HEIGHT:
            quit()

        # Check if bars need to be removed
        new_bars = list()
        for bar in game.bars:
            if bar.rect.y + bar.rect.height/2 < SCREEN_HEIGHT:
                new_bars.append(bar)
        game.bars = new_bars

        self.rect.move_ip(movement)


class Bar(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__()
        self.image = pygame.Surface((BAR_WIDTH, BAR_HEIGHT))
        color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        self.image.fill(color)
        self.rect = self.image.get_rect(x=position[0], y=position[1])

    def update(self, dt):
        pass


player = Player()
bar01 = Bar(position=(100, 400))
bar02 = Bar(position=(140, 300))
bar03 = Bar(position=(100, 420))
bar04 = Bar(position=(70, 200))
bar05 = Bar(position=(160, 100))
bar06 = Bar(position=(100, 500))

list_bars = list()
list_bars.append(bar01)
list_bars.append(bar02)
list_bars.append(bar03)
list_bars.append(bar04)
list_bars.append(bar05)
list_bars.append(bar06)

game = Game(margin_bottom=player.rect.y - 100)
game.bars = list_bars

running = True
while running:
    dt = clock.tick(FPS) / 1000  # Returns milliseconds between each call to 'tick'. The convert time to seconds.
    screen.fill(BLACK)  # Fill the screen with background color.

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                player.is_moving_left = True
                #player.velocity[0] = -200 * dt
            elif event.key == pygame.K_d:
                player.is_moving_right = True
                #player.velocity[0] = 200 * dt
            elif event.key == pygame.K_SPACE:
                print("Space!")
                if not player.is_jumping:
                    player.is_jumping = True
                    player.jumping_time = 0.0
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                player.is_moving_left = False
            elif event.key == pygame.K_d:
                player.is_moving_right = False

    player.update(dt=dt, list_bars=game.bars, game=game)

    #screen.blit(player.image, player.rect)
    screen.blit(player.image, player.rect)
    #screen.blit(player.platform_image, player.platform)

    for bar in game.bars:
        bar.update(dt=dt)
        screen.blit(bar.image, bar.rect)

    pygame.font.init()
    myfont = pygame.font.SysFont('Arial', 20)
    textsurface = myfont.render(str(game.score), False, (255, 255, 255))
    text_rect_obj = textsurface.get_rect()
    #text_rect_obj.center = (0, 0)
    screen.blit(textsurface, text_rect_obj)

    pygame.display.update()  # Or pygame.display.flip()

print("Exited the game loop. Game will quit...")
quit()  # Not actually necessary since the script will exit anyway.da