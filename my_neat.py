import sys
import os
import pickle
import neat
import argparse

from game import Game


def test_model(genome, capture=False):
    local_dir = os.path.dirname(__file__)
    config_file = os.path.join(local_dir, 'config-feedforward.txt')
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)
    net = neat.nn.FeedForwardNetwork.create(genome, config)

    game = Game()
    game.render = True
    game.capture = capture
    game.start(play=False)
    current_score = 0
    steps_since_last_score_change = 0

    while not game.done:

        state = game.step()
        output = net.activate(state)
        action = output.index(max(output))
        game.performAction(action=action)

        if game.player.score == current_score:
            steps_since_last_score_change += 1
        else:
            current_score = game.player.score
            steps_since_last_score_change = 0

        if steps_since_last_score_change > 200:
            game.done = True

    game.end()


def eval_genomes(genomes, config):
    for genome_id, genome in genomes:

        game = Game()
        game.render = True
        game.start(play=False)
        net = neat.nn.FeedForwardNetwork.create(genome, config)

        steps_since_last_score_change = 0
        current_score = 0

        while not game.done:

            state = game.step()

            output = net.activate(state)
            #print(state)
            action = output.index(max(output))
            #print(action)
            game.performAction(action=action)

            if game.player.score == current_score:
                steps_since_last_score_change += 1
            else:
                current_score = game.player.score
                steps_since_last_score_change = 0

            if steps_since_last_score_change > 200:
                game.done = True

        game.end()
        score = 0
        if game.player.score == 0:
            score = 0
        else:
            score = game.player.score

        print("Score: %f" % score)
        genome.fitness = score


def run_with_neat_library():
    # Load configuration.
    local_dir = os.path.dirname(__file__)
    config_file = os.path.join(local_dir, 'config-feedforward.txt')
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(5))

    # Run for up to 300 generations.
    winner = p.run(eval_genomes, 300)

    # Display the winning genome.
    print('\nBest genome:\n{!s}'.format(winner))

    with open('models/best_genome.pkl', 'wb') as handle:
        pickle.dump(winner, handle)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', action='store_true')
    parser.add_argument('--train', action='store_true')
    parser.add_argument('model_path', action='store', type=str, nargs='?', default='models/best_genome.pkl')
    FLAGS, unparsed = parser.parse_known_args()

    if FLAGS.train:
        run_with_neat_library()

    with open(FLAGS.model_path, 'rb') as handle:
        genome = pickle.load(handle)

    test_model(genome, FLAGS.capture)