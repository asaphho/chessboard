from os import path
from classes.move import LegalMove
import PySimpleGUI as sg
import PySimpleGUI.PySimpleGUI
import sys
from classes.position import Position
from utils.board_functions import square_color_int, ALL_SQUARES
from simple_bot.bot1.evaluation import quick_evaluate
from classes.bot import Bot
from version import software_version
from classes.game import Game
from typing import List, Dict, Union

UNHANDLED_ERROR_MESSAGE = 'Something went wrong. :( Immediately after closing this popup, please submit an issue on https://github.com/asaphho/chessboard with the moves of the game up to this point, and describe what you attempted to do.'

TITLE = f'chessboard v{software_version}'
FEN_SYMBOL_TO_PIECE = {'P': 'wpawn', 'K': 'wking', 'Q': 'wqueen', 'B': 'wbishop', 'N': 'wknight', 'R': 'wrook',
                       'p': 'bpawn', 'k': 'bking', 'q': 'bqueen', 'b': 'bbishop', 'n': 'bknight', 'r': 'brook',
                       '1': 'empty'}

intro_text = ('Enter moves in standard algebraic notation, or click on a piece and then a destination square to move it.\n'
              'If using notation, always use uppercase for non-pawn pieces.\n'
              'Give all files in lowercase. Do not include any spaces.\n ')
# buttons: 'Flip board' 'Show moves' 'Show FEN' 'Restart game' 'Take back last move'

ALL_SQUARE_KEYS = []
for i in '01234567':
    for j in '01234567':
        ALL_SQUARE_KEYS.append(i+j)




def main_menu() -> Dict[str, Union[bool, str, None]]:
    main_menu_layout = [[sg.Button('Human VS Human')],
                        [sg.Button('Play against bot')],
                        [sg.Button('Quit to desktop')]]

    bot_menu_layout = [[sg.Text('Play as:'), sg.Radio('White', group_id=1, default=True, key='w'),
                        sg.Radio('Black', group_id=1, key='b')],
                       [sg.Checkbox('Let bot use opening book', default=True, key='op_book')],
                       [sg.Button('OK'), sg.Button('Cancel')]]
    main_menu_window = sg.Window(TITLE, layout=main_menu_layout)
    while True:
        event, values = main_menu_window.read()
        if event == sg.WIN_CLOSED or event == 'Quit to desktop':
            main_menu_window.close()
            return {'exit': True, 'bot': False, 'bot_color': 'b', 'opening_book': None}
        elif event == 'Play against bot':
            main_menu_window.close()
            bot_window = sg.Window(TITLE, bot_menu_layout)
            while True:
                b_event, b_values = bot_window.read()
                if b_event == sg.WIN_CLOSED or b_event == 'Cancel':
                    bot_window.close()
                    return main_menu()
                elif b_event == 'OK':
                    bot_color = 'w' if b_values['w'] is False else 'b'
                    opening_book_path = get_opening_book_path() if b_values['op_book'] is True else None
                    bot_window.close()
                    return {'exit': False, 'bot': True, 'bot_color': bot_color, 'opening_book': opening_book_path}
        elif event == 'Human VS Human':
            main_menu_window.close()
            return {'exit': False, 'bot': False, 'bot_color': 'b', 'opening_book': None}


def generate_position_layout(position: Position) -> List[List]:
    """
    Generates the chessboard part of the layout parameter to be passed into sg.Window when rendering the window.
    Returns a list of 8 lists. Each list in this list corresponds to a rank on the board, while each of the 8
    elements in that list corresponds to a specific square in that rank, and is an sg.Image object, rendering one of the
    26 possible individual square images. Reads the 'flipped' property of the Position object to determine the orientation
    of the rendered board.
    :param position: The Position object to be rendered.
    :return: The chessboard part of the layout of the window, as a list of lists.
    """
    ranks = '87654321' if not position.is_flipped() else '12345678'
    files = 'abcdefgh'if not position.is_flipped() else 'hgfedcba'
    layout = []
    for i in range(len(ranks)):
        rank_layout = []
        for j in range(len(files)):
            curr_square = f'{files[j]}{ranks[i]}'
            filepath = get_image_path_from_square(position, curr_square)
            rank_layout.append(sg.Image(filepath, key=f'{i}{j}', enable_events=True))
        layout.append(rank_layout)
    return layout


def square_to_key(flipped: bool) -> Dict[str, str]:
    """
    Takes in the flipped property of the current position and returns a dictionary mapping each square to its
    corresponding key in the window layout.
    :param flipped: whether the position is flipped.
    :return:
    """
    ranks = '87654321' if not flipped else '12345678'
    files = 'abcdefgh' if not flipped else 'hgfedcba'
    square_to_key_dict = {}
    for i in range(len(ranks)):
        for j in range(len(files)):
            square_to_key_dict[f'{files[j]}{ranks[i]}'] = f'{i}{j}'
    return square_to_key_dict


def key_to_square(flipped: bool) -> Dict[str, str]:
    ranks = '87654321' if not flipped else '12345678'
    files = 'abcdefgh' if not flipped else 'hgfedcba'
    key_to_square_dict = {}
    for i in range(8):
        for j in range(8):
            key_to_square_dict[f'{i}{j}'] = f'{files[j]}{ranks[i]}'
    return key_to_square_dict


def get_square_color(curr_square: str) -> str:
    square_color_bit = square_color_int(curr_square)
    square_color = 'light' if square_color_bit == 0 else 'dark'
    return square_color


def get_path_to_image(filename: str) -> str:
    try:
        filepath = path.join(sys._MEIPASS, 'images', filename)
    except Exception:
        filepath = path.join('.', 'images', filename)
    return filepath


def get_opening_book_path() -> str:
    try:
        filepath = path.join(sys._MEIPASS, 'opening_book', 'fen_uci.json')
    except Exception:
        filepath = path.join('.', 'simple_bot', 'opening_book', 'fen_uci.json')
    return filepath


def get_image_path_from_square(position: Position, square: str, highlight: bool = False) -> str:
    square_color = get_square_color(square)
    square_occupant = position.look_at_square(square)
    piece = FEN_SYMBOL_TO_PIECE[square_occupant]
    hl_suffix = '_hl' if highlight else ''
    filename = f'{square_color}_{piece}{hl_suffix}.png'
    return get_path_to_image(filename)


def side_to_move_text(position: Position) -> str:
    side_to_move = position.to_move()
    side_to_move = 'White' if side_to_move == 'w' else 'Black'
    return f'{side_to_move} to move.'


def update_position_layout_in_window(window: PySimpleGUI.PySimpleGUI.Window, move: LegalMove, flipped: bool) -> None:
    """
    For updating the position part of the layout after a legal move is played WHICH DOES NOT TRIGGER AN END GAME
    CONDITION. This whole design might benefit from some refactoring, but I'm just going to leave it as it is for now.
    :param window:
    :param move:
    :param flipped:
    :return:
    """
    square_to_key_mapping = square_to_key(flipped)
    origin_square = move.origin_square
    piece_color = move.get_color()
    piece_type = move.piece_moved
    destination_square = move.destination_square
    destination_square_color = get_square_color(destination_square)
    origin_square_color = get_square_color(origin_square)
    origin_square_filename = f'{origin_square_color}_empty.png'
    origin_square_filepath = get_path_to_image(origin_square_filename)
    piece_to_name = {'P': 'pawn', 'N': 'knight', 'B': 'bishop', 'R': 'rook', 'Q': 'queen', 'K': 'king'}
    window[square_to_key_mapping[origin_square]].update(filename=origin_square_filepath)
    if not move.pawn_promotion_required():
        destination_square_filename = f'{destination_square_color}_{piece_color}{piece_to_name[piece_type]}.png'
    else:
        destination_square_filename = f'{destination_square_color}_{piece_color}{piece_to_name[move.promotion_piece]}.png'
    destination_square_filepath = get_path_to_image(destination_square_filename)
    window[square_to_key_mapping[destination_square]].update(filename=destination_square_filepath)
    if move.castling != 'N':
        rook_home_file = 'h' if move.castling == 'k' else 'a'
        back_rank = '1' if piece_color == 'w' else '8'
        rook_destination_file = 'f' if move.castling == 'k' else 'd'
        rook_home_square = rook_home_file + back_rank
        rook_home_square_color = get_square_color(rook_home_square)
        rook_home_square_filename = f'{rook_home_square_color}_empty.png'
        rook_home_square_filepath = get_path_to_image(rook_home_square_filename)
        window[square_to_key_mapping[rook_home_square]].update(filename=rook_home_square_filepath)
        rook_destination_square = rook_destination_file + back_rank
        rook_destination_square_color = get_square_color(rook_destination_square)
        rook_destination_square_filename = f'{rook_destination_square_color}_{piece_color}rook.png'
        rook_destination_square_filepath = get_path_to_image(rook_destination_square_filename)
        window[square_to_key_mapping[rook_destination_square]].update(filename=rook_destination_square_filepath)
    if move.is_en_passant_capture():
        captured_pawn_rank = '5' if piece_color == 'w' else '4'
        captured_pawn_square = destination_square[0] + captured_pawn_rank
        captured_pawn_square_color = get_square_color(captured_pawn_square)
        captured_pawn_square_filename = f'{captured_pawn_square_color}_empty.png'
        captured_pawn_square_filepath = get_path_to_image(captured_pawn_square_filename)
        window[square_to_key_mapping[captured_pawn_square]].update(filename=captured_pawn_square_filepath)
    window.refresh()


def generate_layout(game: Game, output_from_prev_input: str = '', game_end_text: str = None) -> List[List]:
    """
    Generates the layout to be passed to the sg.Window constructor to render the window. Has the following sections,
    from top to bottom:
        - Intro text.
        - Side to move. If game is over, shows "Game is over" instead.
        - The chessboard showing the current position.
        - output_from_prev_input: Depending on the last action, it could be the last move played, the FEN of the current position, or an error message from an invalid input.
        - Field to input the move in standard algebraic notation, followed by the button 'Enter move'. If the game is over, this section is replaced by a text line showing game_end_text.
        - The row of buttons: Flip board, Show moves, Show FEN, Restart game, Take back last move.

    :param game:
    :param output_from_prev_input:
    :param game_end_text: should be None if the game is not over yet.
    :return: The full layout object to be passed to the sg.Window constructor.
    """
    position = game.current_position
    layout = [[sg.Text(intro_text)]]
    if game_end_text is None:
        layout += [[sg.Text(side_to_move_text(position), key='-TOMOVE-')]]
    else:
        layout += [[sg.Text('Game is over.', key='-TOMOVE-')]]
    position_layout = generate_position_layout(position)
    layout += position_layout
    layout += [[sg.Text(output_from_prev_input, key='-TEXT-')]]
    if game_end_text is None:
        prompt = create_input_move_prompt(game)
        layout += [[sg.Text('', key='-GAMEENDTEXT-', visible=True)]]
        layout += [[sg.Text(prompt, key='-INPUTPROMPT-', visible=True), sg.InputText(key='-INPUT-', focus=True, visible=True), sg.Button('Enter move', bind_return_key=True, visible=True)]]
    else:
        layout += [[sg.Text(game_end_text, key='-GAMEENDTEXT-', visible=True)]]
        layout += [
            [sg.Text('', key='-INPUTPROMPT-', visible=False), sg.InputText(key='-INPUT-', focus=True, visible=False),
             sg.Button('Enter move', bind_return_key=True, visible=False)]]
    layout += [[sg.Button('Flip board'), sg.Button('Show moves'), sg.Button('Show FEN'), sg.Button('Restart game'), sg.Button('Take back last move')]]
    return layout


def update_layout(game: Game, window: PySimpleGUI.PySimpleGUI.Window, output_from_prev: str = '', input_text: str = None, game_end_text: str = None) -> None:
    """
    Updates the layout after flipping board, taking back last move, ending the game, or restarting the game
    :param input_text: The text currently in the input field (-INPUT-). Should be preserved when flipping board and the game is not over yet.
    :param window:
    :param game:
    :param output_from_prev:
    :param game_end_text:
    :return:
    """
    position = game.current_position
    flipped = position.is_flipped()
    square_to_key_mapping = square_to_key(flipped)
    if game_end_text is None:
        window['-TOMOVE-'].update(side_to_move_text(position))
    else:
        window['-TOMOVE-'].update('Game is over.')
    for square in ALL_SQUARES:
        key_in_layout = square_to_key_mapping[square]
        image_filepath = get_image_path_from_square(position, square)
        window[key_in_layout].update(filename=image_filepath)
    window['-TEXT-'].update(output_from_prev)
    if game_end_text is None:
        prompt = create_input_move_prompt(game)
        window['-GAMEENDTEXT-'].update('', visible=True)
        window['-INPUTPROMPT-'].update(prompt, visible=True)
        window['-INPUT-'].update('' if input_text is None else input_text, visible=True)
        window['Enter move'].update(visible=True)
    else:
        window['-GAMEENDTEXT-'].update(game_end_text, visible=True)
        window['-INPUTPROMPT-'].update(visible=False)
        window['-INPUT-'].update(visible=False)
        window['Enter move'].update(visible=False)
    window.refresh()


def create_input_move_prompt(game):
    to_move = game.current_position.to_move()
    move_number = game.current_position.get_move_number()
    prompt = f'{move_number}'
    if to_move == 'w':
        prompt += '. '
    else:
        prompt += '... '
    return prompt


def play_computer_move(bot, game, window):
    window['-TEXT-'].update('Bot is thinking.')
    bot_color = game.current_position.to_move()
    res, move = game.play_computer_move(bot, True)
    game_end_check = game.check_game_end_conditions()
    if game_end_check == 'N':
        update_window_layout_after_move_game_continues(game, move, res, window)
        return False
    else:
        update_layout(game, window, res, game_end_text=game_end_check)
        exit_signal = enter_game_end_loop(game, game_end_check, window, bot=bot, bot_color=bot_color, game_ended_by_bot=True)
        return exit_signal


def display_moves(game: Game) -> None:
    moves = game.show_moves(return_string_for_window=True)
    new_window_layout = [[sg.Text(moves)]]
    new_window = sg.Window('Moves', new_window_layout, finalize=True)


def main(game):
    main_menu_results = main_menu()
    if main_menu_results['exit'] is True:
        sys.exit()

    bot_color = main_menu_results['bot_color']
    playing_against_bot = main_menu_results['bot']
    if playing_against_bot:
        bot = Bot(quick_evaluate, 3, 1, 0.15, opening_book_path=main_menu_results['opening_book'])
    else:
        bot = None
    if playing_against_bot and bot_color == 'w':
        res = game.play_computer_move(bot)
        game.current_position.flip_position()
        layout = generate_layout(game, res)
    else:
        layout = generate_layout(game)
    window = sg.Window(TITLE, layout, element_padding=(0, 0))
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event == 'Flip board':
            game.current_position.flip_position()
            text = window['-TEXT-'].DisplayText
            input_text = values['-INPUT-']
            update_layout(game, window, text, input_text=input_text)
        elif event == 'Show moves':
            display_moves(game)
        elif event == 'Show FEN':
            window['-TEXT-'].update(game.current_position.generate_fen())
        elif event == 'Restart game':
            if sg.popup_yes_no('Are you sure you want to restart?') == 'Yes':
                game.restart_game()
                if playing_against_bot and bot_color == 'w':
                    res = game.play_computer_move(bot)
                    game.current_position.flip_position()
                    update_layout(game, window, res)
                else:
                    update_layout(game, window, 'Game restarted.')
        elif event == 'Take back last move':
            if not playing_against_bot:
                text = game.take_back_last_move(silent=True)
                update_layout(game, window, text)
            elif playing_against_bot and bot_color == 'w' and game.current_position.move_number == 1:
                window['-TEXT-'].update('Nothing to take back.')
            else:
                game.take_back_last_move(silent=True)
                text = game.take_back_last_move(silent=True)
                update_layout(game, window, text)

        elif event == 'Enter move':
            input_notation = values['-INPUT-'].strip()
            if input_notation == '':
                continue
            try:
                res, move = game.process_input_notation(input_notation, return_move_for_gui=True)
            except Exception as e:
                window['-TEXT-'].update(str(e))
                continue
            game_end_check = game.check_game_end_conditions()
            if game_end_check == 'N':
                update_window_layout_after_move_game_continues(game, move, res, window)
                if playing_against_bot:
                    exit_signal = play_computer_move(bot, game, window)
                    if exit_signal:
                        break
            else:
                update_layout(game, window, res, game_end_text=game_end_check)
                exit_signal = enter_game_end_loop(game, game_end_check, window, bot=bot, bot_color=bot_color)
                if exit_signal:
                    break
        elif event in ALL_SQUARE_KEYS:
            first_clicked_square_key = event
            key_to_square_dict = key_to_square(game.current_position.is_flipped())
            first_clicked_square = key_to_square_dict[event]
            to_move = game.current_position.to_move()
            if first_clicked_square not in game.current_position.get_pieces_by_color(to_move).get_occupied_squares():
                continue
            window[event].update(filename=get_image_path_from_square(game.current_position, first_clicked_square, highlight=True))
            window.refresh()
            exit_signal = False
            while True:
                event, values = window.read()
                if event == sg.WIN_CLOSED:
                    exit_signal = True
                    break
                if event == 'Flip board':
                    game.current_position.flip_position()
                    text = window['-TEXT-'].DisplayText
                    input_text = values['-INPUT-']
                    update_layout(game, window, text, input_text=input_text)
                    break
                elif event == 'Show moves':
                    display_moves(game)
                elif event == 'Show FEN':
                    window['-TEXT-'].update(game.current_position.generate_fen())
                elif event == 'Restart game':
                    if sg.popup_yes_no('Are you sure you want to restart?') == 'Yes':
                        game.restart_game()
                        if playing_against_bot and bot_color == 'w':
                            res = game.play_computer_move(bot)
                            game.current_position.flip_position()
                            update_layout(game, window, res)
                            break
                        else:
                            update_layout(game, window, 'Game restarted.')
                            break
                elif event == 'Take back last move':
                    if not playing_against_bot:
                        text = game.take_back_last_move(silent=True)
                        update_layout(game, window, text)
                    elif playing_against_bot and bot_color == 'w' and game.current_position.move_number == 1:
                        window['-TEXT-'].update('Nothing to take back.')
                    else:
                        game.take_back_last_move(silent=True)
                        text = game.take_back_last_move(silent=True)
                        update_layout(game, window, text)
                    break
                elif event == 'Enter move':
                    window['-TEXT-'].update('Moving by notation is disabled when a piece has been selected.')
                elif event in ALL_SQUARE_KEYS:
                    second_clicked_square = key_to_square_dict[event]
                    if first_clicked_square == second_clicked_square:
                        window[first_clicked_square_key].update(
                            filename=get_image_path_from_square(game.current_position, first_clicked_square))
                        window.refresh()
                        break
                    all_legal_moves = game.current_position.get_all_legal_moves_for_color(to_move)
                    possible_legal_moves = [move for move in all_legal_moves if move.origin_square == first_clicked_square and move.destination_square == second_clicked_square]
                    if len(possible_legal_moves) == 0:
                        window['-TEXT-'].update('Illegal move.')
                        window[first_clicked_square_key].update(filename=get_image_path_from_square(game.current_position, first_clicked_square))
                        window.refresh()
                        break
                    else:
                        first_possible_move = possible_legal_moves[0]
                        if not first_possible_move.pawn_promotion_required():
                            move = first_possible_move
                        else:
                            result = sg.popup_get_text('Select promotion piece by entering Q, R, N, or B. Only first character will be taken.',
                                                       default_text='Q', title='Select promotion piece')

                            if result is None:
                                window[first_clicked_square_key].update(
                                    filename=get_image_path_from_square(game.current_position, first_clicked_square))
                                window.refresh()
                                break
                            result = result[0].upper()
                            possible_moves = [m for m in possible_legal_moves if m.promotion_piece == result]
                            if len(possible_moves) == 0:
                                sg.popup('Invalid promotion piece symbol')
                                window[first_clicked_square_key].update(
                                    filename=get_image_path_from_square(game.current_position,
                                                                        first_clicked_square))
                                window.refresh()
                                break
                            else:
                                move = possible_moves[0]

                        res = game.process_move(move)
                        game_end_check = game.check_game_end_conditions()
                        if game_end_check == 'N':
                            update_window_layout_after_move_game_continues(game, move, res, window)
                            if playing_against_bot:
                                exit_signal = play_computer_move(bot, game, window)
                                if exit_signal:
                                    break
                            break
                        else:
                            update_layout(game, window, res, game_end_text=game_end_check)
                            exit_signal = enter_game_end_loop(game, game_end_check, window, bot=bot, bot_color=bot_color)
                            break
            if exit_signal:
                break
    window.close()


def update_window_layout_after_move_game_continues(game, move, res, window):
    update_position_layout_in_window(window, move, game.current_position.is_flipped())
    window['-TEXT-'].update(res)
    window['-INPUT-'].update('')
    window['-INPUTPROMPT-'].update(create_input_move_prompt(game))
    window['-TOMOVE-'].update(side_to_move_text(game.current_position))


def enter_game_end_loop(game: Game, game_end_check: str, window: PySimpleGUI.PySimpleGUI.Window, bot: Bot = None,
                        game_ended_by_bot: bool = False, bot_color: str = 'b') -> bool:
    exit_signal = False
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            exit_signal = True
            break
        elif event == 'Flip board':
            game.current_position.flip_position()
            text = window['-TEXT-'].DisplayText
            update_layout(game, window, text, game_end_text=game_end_check)
        elif event == 'Show moves':
            display_moves(game)
        elif event == 'Show FEN':
            window['-TEXT-'].update(game.current_position.generate_fen())
        elif event == 'Restart game':
            if sg.popup_yes_no('Are you sure you want to restart?') == 'Yes':
                game.restart_game()
                if bot and bot_color == 'w':
                    res = game.play_computer_move(bot)
                    game.current_position.flip_position()
                    update_layout(game, window, res)
                else:
                    update_layout(game, window, 'Game restarted.')
                break
        elif event == 'Take back last move':
            text = game.take_back_last_move(silent=True)
            update_layout(game, window, text)
            if bot and game_ended_by_bot:
                text = game.take_back_last_move(silent=True)
                update_layout(game, window, text)
            break
    return exit_signal


if __name__ == '__main__':
    new_game = Game()
    main(new_game)






