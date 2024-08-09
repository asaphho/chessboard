from classes.game import Game
from classes.bot import Bot
import simple_bot.bot1.evaluation as bot1_params
import simple_bot.bot2.evaluation as bot2_params

bot1 = Bot(bot1_params.evaluate)
bot2 = Bot(bot2_params.evaluate)
players = {'w': bot1, 'b': bot2}
game = Game()

while True:
    player = players[game.current_position.to_move()]
    res = game.play_computer_move(player)
    print(res)
    game_end_check = game.check_game_end_conditions()
    if game_end_check != 'N':
        print(game_end_check)
        game.show_moves()
        break
