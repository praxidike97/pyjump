import sys
import os
import time
import pickle
import numpy as np
from tqdm import tqdm
import neat

from game import Game


class Agent():
    def __init__(self, input_size=6, output_size=3):
        self.hidden_weights = None
        self.output_weights = None

        self.hidden_size = 4

        self.hidden_weights = np.random.uniform(-1., 1., (self.hidden_size, input_size + 1))
        self.output_weights = np.random.uniform(-1., 1., (output_size, self.hidden_size + 1))
        #self.hidden_weights = np.random.rand(self.hidden_size, input_size + 1)
        #self.output_weights = np.random.rand(output_size, self.hidden_size + 1)

        self.weight_matrices = [self.hidden_weights, self.output_weights]

        # The score this agent achieved in the game
        self.score = 0

    def set_weights(self, weight_matrices):
        self.hidden_weights = weight_matrices[0]
        self.output_weights = weight_matrices[1]

        self.weight_matrices = [self.hidden_weights, self.output_weights]

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def softmax(self, x):
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum(axis=0)

    def predict(self, x):
        # Add one value for the bias
        x = np.append(x, 1.)
        x = np.dot(self.hidden_weights, x)
        x = self.sigmoid(x)
        x = np.append(x, 1.)
        x = np.dot(self.output_weights, x)
        x = self.softmax(x)
        return np.argmax(x)

    def save(self):
        with open('best_agent.pkl', 'wb') as handle:
            pickle.dump(self, handle)


class NEAT():
    def __init__(self, population_size=100):
        self.population_size = population_size
        self.agents = list()

        for _ in range(self.population_size):
            self.agents.append(Agent())

    # Creates the next generation of agents
    def next_generation(self):
        # Calculate the normalized scores of the agents
        scores = np.array([agent.score for agent in self.agents])

        if np.sum(scores) != 0:
            scores = scores/np.sum(scores)

        new_population = list()
        for i in range(self.population_size):
            agent01 = np.random.choice(self.agents, p=scores)
            agent02 = np.random.choice(self.agents, p=scores)

            new_agent = self.crossover(agent01, agent02)
            new_agent = self.mutate(new_agent, 0.3)
            new_population.append(new_agent)

        self.agents = new_population

    def crossover(self, agent01, agent02):
        new_weights_matrices = list()

        for i in range(len(agent01.weight_matrices)):
            weight_matrix = np.zeros((agent01.weight_matrices[i].shape[0], agent02.weight_matrices[i].shape[1]))
            x = agent01.weight_matrices[i].shape[0] // 2
            weight_matrix[:x], weight_matrix[x:] = agent01.weight_matrices[i][:x], agent02.weight_matrices[i][x:]

            new_weights_matrices.append(weight_matrix)

        new_agent = Agent()
        new_agent.set_weights(weight_matrices=new_weights_matrices)
        return new_agent

    def mutate(self, agent, rate):
        for k in range(len(agent.weight_matrices)):
            for i in range(agent.weight_matrices[k].shape[0]):
                if rate > (np.random.uniform(0, 1)):
                    for j in range(agent.weight_matrices[k].shape[1]):
                        agent.weight_matrices[k][i][j] += np.random.uniform(-1, 1)
        return agent


def test(genome):
    local_dir = os.path.dirname(__file__)
    config_file = os.path.join(local_dir, 'config-feedforward.txt')
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)
    net = neat.nn.FeedForwardNetwork.create(genome, config)

    game = Game()
    game.render = True
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

    with open('best_genome.pkl', 'wb') as handle:
        pickle.dump(winner, handle)

    """
    # Show output of the most fit genome against training data.
    print('\nOutput:')
    winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
    for xi, xo in zip(xor_inputs, xor_outputs):
        output = winner_net.activate(xi)
        print("input {!r}, expected output {!r}, got {!r}".format(xi, xo, output))

    node_names = {-1: 'A', -2: 'B', 0: 'A XOR B'}
    visualize.draw_net(config, winner, True, node_names=node_names)
    visualize.plot_stats(stats, ylog=False, view=True)
    visualize.plot_species(stats, view=True)

    p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-4')
    p.run(eval_genomes, 10)
    """


if __name__ == "__main__":
    #run_with_neat_library()

    with open('best_agent.pkl', 'rb') as handle:
        genome = pickle.load(handle)

    test(genome)
    sys.exit(0)

    epochs = 50
    best_score = 0
    neat = NEAT(population_size=200)
    step_counter = 0

    for e in range(epochs):
        all_scores = list()
        for agent in tqdm(neat.agents):

            game = Game()
            game.render = False
            game.start(play=False)
            current_score = 0
            steps_since_last_score_change = 0

            while not game.done:

                state = game.step()
                #print("State: %s" % str(state))
                action = agent.predict(np.array(state))
                game.performAction(action=action)
                step_counter += 1

                if game.player.score == current_score:
                    steps_since_last_score_change += 1
                else:
                    current_score = game.player.score
                    steps_since_last_score_change = 0

                if steps_since_last_score_change > 200:
                    game.done = True

            game.end()

            if game.player.score == 0:
                agent.score = 10
            else:
                agent.score = game.player.score

            if agent.score > best_score:
                agent.save()
                best_score = agent.score

            print("Score: %i" % game.player.score)
            all_scores.append(game.player.score)

        print("Epoch: %i  Max score: %i" % (e, max(all_scores)))
        neat.next_generation()