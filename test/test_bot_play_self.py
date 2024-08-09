from classes.game import Game

game = Game()

while True:
    res = game.play_computer_move()
    print(res)
    game_end_check = game.check_game_end_conditions()
    if game_end_check != 'N':
        print(game_end_check)
        game.show_moves()
        break
