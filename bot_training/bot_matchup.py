from classes.bot import Bot
from classes.game import Game
from typing import Dict
from simple_bot.bot1.evaluation import quick_evaluate


def run_match(training_bot: Bot, opposing_bot: Bot, n_rounds: int = 12) -> str:
    training_bot_score = 0
    opposing_bot_score = 0
    white_bot = 't'
    black_bot = 'o'
    for i in range(n_rounds):
        game = Game()
        game_end_condition = game.check_game_end_conditions()
        while game_end_condition == 'N':
            side_to_move = game.current_position.to_move()
            if side_to_move.lower().startswith('w'):
                bot_to_play = white_bot
            else:
                bot_to_play = black_bot
            game.play_computer_move(training_bot if bot_to_play == 't' else opposing_bot)
            game_end_condition = game.check_game_end_conditions()
        if game_end_condition.lower().startswith('white'):
            winning_bot = white_bot
        elif game_end_condition.lower().startswith('black'):
            winning_bot = black_bot
        else:
            winning_bot = 'n'
        if winning_bot == 't':
            training_bot_score += 1
        elif winning_bot == 'o':
            opposing_bot_score += 1
        else:
            training_bot_score += 0.5
            opposing_bot_score += 0.5
        white_bot, black_bot = black_bot, white_bot
        print(f'A game has been completed. ({i+1}/{n_rounds})')
    if training_bot_score > opposing_bot_score:
        result = '1-0'
    elif opposing_bot_score > training_bot_score:
        result = '0-1'
    else:
        result = '0.5-0.5'
    print('A match has been completed.')
    return result


def compare_configs(config1: Dict[int, float], config2: Dict[int, float]) -> str:
    bot1 = Bot(evaluation_func=quick_evaluate, bot_params=config1, fluctuation=0.15)
    bot2 = Bot(evaluation_func=quick_evaluate, bot_params=config2, fluctuation=0.15)
    return run_match(bot1, bot2, 6)
