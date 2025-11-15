from bot_training import BOT_TRAINING_DIR
from os import path
import json
from bot_training.utils import numerify_json_keys
from datetime import datetime
from bot_training.bot_matchup import compare_configs
import multiprocessing as mp
import sys
from bot_training.round_robin import generate_pairings, rank_all_players
from bot_training.swiss_tournament import update_round_results
from bot_training.utils import breed_offspring_from_pool

N_PROCESSES = int(sys.argv[1])
N_GAMES_PER_MATCH = 4
MUTATION_STRENGTH = 0.05
MUTATION_PROBABILITY = 0.1
ELITES_TO_KEEP = 2
BREEDING_FOR_NEXT_GEN = 5


if __name__ == '__main__':
    with open(path.join(BOT_TRAINING_DIR, 'round_robin_pool.json'), 'r') as f:
        players = json.load(f)

    player_configs = [numerify_json_keys(config) for config in players]
    n_players = len(players)
    n_rounds = n_players - 1

    curr_results = {}
    for i in range(n_players):
        curr_results[i] = []

    for i in range(n_rounds):
        print(f'Round {i + 1} started: {datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")}', flush=True)
        pairings_for_round = generate_pairings(curr_results)
        print(f'Pairings for round {i + 1}:\n{json.dumps(pairings_for_round, indent=4)}')
        config_pairings = [(player_configs[pairing[0]], player_configs[pairing[1]], N_GAMES_PER_MATCH) for pairing in pairings_for_round]
        with mp.Pool(processes=N_PROCESSES) as pool:
            round_results = pool.starmap(compare_configs, config_pairings)
        pairings_results = [(pairings_for_round[i][0], pairings_for_round[i][1], round_results[i]) for i in range(len(pairings_for_round))]
        print(f'Results of round {i + 1}:\n{json.dumps(pairings_results, indent=4)}')
        update_round_results(curr_results, pairings_results)

    final_rankings = rank_all_players(curr_results)
    print(f'Final results:\n{json.dumps(curr_results)}')
    print(f'Final rankings: {final_rankings}')

    for_breeding = final_rankings[:BREEDING_FOR_NEXT_GEN]
    configs_for_breeding = [player_configs[i] for i in for_breeding]
    elites = for_breeding[:ELITES_TO_KEEP]
    elite_configs = [player_configs[i] for i in elites]
    offspring = breed_offspring_from_pool(parents=configs_for_breeding,
                                          n_offspring=n_players - ELITES_TO_KEEP,
                                          mutation_prob=MUTATION_PROBABILITY,
                                          mutation_strength=MUTATION_STRENGTH)
    next_gen = elite_configs + offspring
    with open(path.join(BOT_TRAINING_DIR, 'round_robin_pool.json'), 'w') as w:
        w.write(json.dumps(next_gen, indent=4))

    with open(path.join(BOT_TRAINING_DIR, 'curr_gen.txt'), 'r') as r:
        lines = r.readlines()
        curr_gen = int(lines[0][0])

    curr_gen += 1

    with open(path.join(BOT_TRAINING_DIR, 'curr_gen.txt'), 'w') as w:
        w.write(str(curr_gen))

