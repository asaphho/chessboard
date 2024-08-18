from classes.game import Game
from classes.bot import Bot
import simple_bot.bot1.evaluation as bot1_params

bot1 = Bot(bot1_params.quick_evaluate, breadth=3, aggression=1, ply_depth=4)
bot2 = Bot(bot1_params.quick_evaluate, breadth=3, aggression=1, ply_depth=5)
players = {'w': bot1, 'b': bot2}
game = Game()

while True:
    player = players[game.current_position.to_move()]
    res = game.play_computer_move(player)
    print(res)
    game_end_check = game.check_game_end_conditions()
    if game_end_check != 'N':
        game.show_moves()
        print(game.current_position.generate_fen())
        print(game_end_check)
        break
