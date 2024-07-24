from classes.game import Game

intro_text = ('Enter moves in standard algebraic notation. Always use uppercase for non-pawn pieces. '
              'Give all files in lowercase. \n '
              'Commands: /showmoves /showfen /restart /help')


def main(game: Game):
    print(intro_text)
    while True:
        to_move = game.current_position.to_move()
        move_number = game.current_position.get_move_number()
        prompt = f'{move_number}'
        if to_move == 'white':
            prompt += '. '
        else:
            prompt += '... '
        input_str = input(prompt).strip()

        if input_str.startswith('/'):
            handle_command(game, input_str)

        else:
            try:
                res = game.process_input_notation(input_str)
                print(res)
            except Exception:
                continue
            end_game_check = game.check_game_end_conditions()
            if end_game_check != 'None':
                print(end_game_check)
                while True:
                    command = input().strip()
                    resume_game_loop = handle_command(game, command)
                    if resume_game_loop:
                        break


def handle_command(game, input_str):
    if input_str.lower() == '/showmoves':
        game.show_moves()
        return False

    elif input_str.lower() == '/showfen':
        fen = game.current_position.generate_fen()
        print(fen)
        return False

    elif input_str.lower() == '/help':
        print(intro_text)
        return False

    elif input_str.lower() == '/restart':
        print('Restarting game.')
        game.restart_game()
        return True

    elif input_str.lower() == '/takeback':
        game.take_back_last_move()
        return True

    else:
        print('Unrecognized command.')


if __name__ == '__main__':
    game = Game()
    main(game)
