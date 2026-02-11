from classes.bot import Bot
from classes.game import Game
from typing import Dict
from simple_bot.bot1.evaluation import quick_evaluate as quick_evaluate1
from datetime import datetime


def run_match(bot1: Bot, bot2: Bot, n_rounds: int = 12, print_moves: bool = False) -> str:
    bot1_name = 'Bot1' if bot1.get_name() is None else bot1.get_name()
    bot2_name = 'Bot2' if bot2.get_name() is None else bot2.get_name()
    if bot1_name == bot2_name:
        raise ValueError('Both bots need to have different names.')
    bot1_score = 0
    bot2_score = 0
    white_bot = '1'
    black_bot = '2'
    for i in range(n_rounds):
        game = Game()
        game_end_condition = game.check_game_end_conditions()
        if print_moves:
            if white_bot == '1':
                print(f'{bot1_name} - {bot2_name}')
            else:
                print(f'{bot2_name} - {bot1_name}')
        while game_end_condition == 'N':
            side_to_move = game.current_position.to_move()
            if side_to_move.lower().startswith('w'):
                bot_to_play = white_bot
            else:
                bot_to_play = black_bot
            move_notation = game.play_computer_move(bot1 if bot_to_play == '1' else bot2)
            if print_moves:
                print(move_notation)
            game_end_condition = game.check_game_end_conditions()
        if game_end_condition.lower().startswith('white'):
            winning_bot = white_bot
            if print_moves:
                print(f'White ({bot1_name if white_bot == "1" else bot2_name}) wins.')
        elif game_end_condition.lower().startswith('black'):
            winning_bot = black_bot
            if print_moves:
                print(f'Black ({bot1_name if black_bot == "1" else bot2_name}) wins.')
        else:
            winning_bot = 'n'
            if print_moves:
                print('Game drawn.')
        if winning_bot == '1':
            bot1_score += 1
        elif winning_bot == '2':
            bot2_score += 1
        else:
            bot1_score += 0.5
            bot2_score += 0.5
        if print_moves:
            print(f'{bot1_name}: {bot1_score}')
            print(f'{bot2_name}: {bot2_score}')
        white_bot, black_bot = black_bot, white_bot
        print(f'A game has been completed in {max(game.moves_record.keys())} moves. ({i+1}/{n_rounds})', flush=True)
    if bot1_score > bot2_score:
        result = '1-0'
    elif bot2_score > bot1_score:
        result = '0-1'
    else:
        result = '0.5-0.5'
    print(f'A match has been completed: {datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")}', flush=True)
    return result


def compare_configs(config1: Dict[int, float], config2: Dict[int, float], n_rounds: int = 6,
                    evaluation_func=quick_evaluate1) -> str:
    bot1 = Bot(evaluation_func=evaluation_func, bot_params=config1, fluctuation=0.12)
    bot2 = Bot(evaluation_func=evaluation_func, bot_params=config2, fluctuation=0.12)
    return run_match(bot1, bot2, n_rounds=n_rounds)
