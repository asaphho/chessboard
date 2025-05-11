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
