from game import Game
import time

game = Game()
game.start(play=False)
print("Nach start!")

step_counter = 0
while True:
    if step_counter < 40:
        game.moveRight()

    state = game.step()
    print(state)

    if game.done:
        quit()

    print(step_counter)
    step_counter += 1
    #time.sleep(0.1)