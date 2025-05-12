import multiprocessing as mp
from bot_training import BOT_TRAINING_DIR
from os import path
import json
from datetime import datetime
from bot_training.swiss_tournament import generate_pairings, update_round_results, rank_all_players
from bot_training.bot_matchup import compare_configs
from bot_training.utils import breed_offspring_from_pool, numerify_json_keys
import sys

N_PROCESSES = int(sys.argv[1])
TOURNAMENT_SIZE = 32
TOURNAMENT_ROUNDS = 4
SELECTED_FOR_BREEDING = 10
ELITES = 2
MUTATION_PROB = 0.1
MUTATION_STR = 0.05
STARTING_POOL_PATH = path.join(BOT_TRAINING_DIR, 'starting_pool.json')

if __name__ == '__main__':
    with open(STARTING_POOL_PATH, 'r') as f:
        starting_pool = json.load(f)

    starting_pool = [numerify_json_keys(config) for config in starting_pool]

    player_results = {}
    for i in range(TOURNAMENT_SIZE):
        player_results[i] = []

    for round_number in range(TOURNAMENT_ROUNDS):
        print(f'Round {round_number + 1} started: {datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")}')
        pairings = generate_pairings(player_results)
        print(f'Pairings for round {round_number + 1}: \n{json.dumps(pairings, indent=4)}')
        config_pairings = [(starting_pool[pairings[i][0]], starting_pool[pairings[i][1]]) for i in range(len(pairings))]
        with mp.Pool(processes=N_PROCESSES) as pool:
            round_results = pool.starmap(compare_configs, config_pairings)
        pairings_results = [(pairings[i][0], pairings[i][1], round_results[i]) for i in range(len(round_results))]
        print(f'Results of round {round_number + 1}: \n{json.dumps(pairings_results, indent=4)}')
        update_round_results(player_results, pairings_results)

    print(f'Final tournament results: \n{json.dumps(player_results, indent=4)}')
    final_rank = rank_all_players(player_results)
    print(f'Final ranking: \n{final_rank}')
    bots_for_breeding = final_rank[:SELECTED_FOR_BREEDING]
    elite_bots = bots_for_breeding[:ELITES]
    configs_for_breeding = [starting_pool[i] for i in bots_for_breeding]
    elite_configs = [starting_pool[i] for i in elite_bots]
    next_starting_pool = elite_configs + breed_offspring_from_pool(parents=configs_for_breeding,
                                                                   n_offspring=TOURNAMENT_SIZE - ELITES,
                                                                   mutation_prob=MUTATION_PROB,
                                                                   mutation_strength=MUTATION_STR)
    with open(STARTING_POOL_PATH, 'w') as w:
        w.write(json.dumps(next_starting_pool, indent=4))

