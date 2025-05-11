from typing import Dict

from bot_training import BOT_TRAINING_DIR
import os
import json
from bot_training.utils import numerify_json_keys

population_config_path = os.path.join(BOT_TRAINING_DIR, 'starting_pool.json')
with open(population_config_path, 'r') as f:
    population = json.load(f)

population = [numerify_json_keys(config) for config in population]
n_parameters = len(population[0])
population_size = len(population)


def standard_dev() -> None:
    means = {}

    for i in range(n_parameters):
        means[i] = 0
        for j in range(population_size):
            means[i] += population[j][i] / population_size

    standard_deviations = {}

    for i in range(n_parameters):
        standard_deviations[i] = 0
        for j in range(population_size):
            standard_deviations[i] += (population[j][i] - means[i]) ** 2 / population_size
        standard_deviations[i] **= 0.5

    print(f'Standard deviations: \n{json.dumps(standard_deviations, indent=4)}')

    average_standard_dev = sum([standard_deviations[i] for i in standard_deviations]) / n_parameters

    print(f'Average standard deviation: {average_standard_dev}')


def mean_pairwise_distance() -> None:
    pairings = []
    for i in range(population_size - 1):
        for j in range(i + 1, population_size):
            pairings.append((i, j))

    def pairwise_distance(config1: Dict[int, float], config2: Dict[int, float]) -> float:
        sum_diff_squares = 0
        for i in config1:
            diff = config1[i] - config2[i]
            sum_diff_squares += diff ** 2
        return sum_diff_squares ** 0.5

    mean_pw_dist = 0
    for pairing in pairings:
        config1 = population[pairing[0]]
        config2 = population[pairing[1]]
        mean_pw_dist += pairwise_distance(config1, config2) / len(pairings)
    print(f'Mean pairwise distance: {mean_pw_dist}')
