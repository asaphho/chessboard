from bot_training import BOT_TRAINING_DIR
from os import path
from bot_training.bot_matchup import run_match
import sys
from classes.bot import Bot
from simple_bot.bot1.evaluation import quick_evaluate
import json
from bot_training.utils import numerify_json_keys

if __name__ == '__main__':
    with open(path.join(BOT_TRAINING_DIR, 'reference_bots', 'default_params.json'), 'r') as f:
        default_params = numerify_json_keys(json.load(f))

    with open(path.join(BOT_TRAINING_DIR, 'curr_gen.txt'), 'r') as f:
        curr_gen = int(f.readlines()[0].strip())

    with open(path.join(BOT_TRAINING_DIR, 'round_robin_pool.json'), 'r') as f:
        curr_gen_params = numerify_json_keys(json.load(f)[0])

    default_bot = Bot(evaluation_func=quick_evaluate, fluctuation=0.12, bot_params=default_params, name='Default Bot')
    curr_gen_bot = Bot(evaluation_func=quick_evaluate, fluctuation=0.12, bot_params=curr_gen_params, name=f'Gen {curr_gen} Bot')

    n_rounds = int(sys.argv[1])

    run_match(default_bot, curr_gen_bot, n_rounds=n_rounds, print_moves=True)
