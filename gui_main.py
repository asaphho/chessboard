from os import path
from classes.move import LegalMove
import PySimpleGUI as sg
import PySimpleGUI.PySimpleGUI
import sys
from classes.position import Position
from utils.board_functions import square_color_int
from version import software_version
from classes.game import Game
from typing import List

TITLE = f'chessboard v{software_version}'
FEN_SYMBOL_TO_PIECE = {'P': 'wpawn', 'K': 'wking', 'Q': 'wqueen', 'B': 'wbishop', 'N': 'wknight', 'R': 'wrook',
                       'p': 'bpawn', 'k': 'bking', 'q': 'bqueen', 'b': 'bbishop', 'n': 'bknight', 'r': 'brook',
                       '1': 'empty'}

intro_text = ('Enter moves in standard algebraic notation. Always use uppercase for non-pawn pieces.\n '
              'Give all files in lowercase. Do not include any spaces.\n ')
# buttons: 'Flip board' 'Show moves' 'Show FEN' 'Restart game' 'Take back last move'
game = Game()


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
    for r in ranks:
        rank_layout = []
        for f in files:
            curr_square = f'{f}{r}'
            square_color = get_square_color(curr_square)
            piece_at_square = position.look_at_square(curr_square)
            filename = f'{square_color}_{FEN_SYMBOL_TO_PIECE[piece_at_square]}.png'
            filepath = get_path_to_image(filename)
            rank_layout.append(sg.Image(filepath, key=curr_square))
        layout.append(rank_layout)
    return layout


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


def update_position_layout_in_window(window: PySimpleGUI.PySimpleGUI.Window, move: LegalMove) -> None:
    origin_square = move.origin_square
    piece_color = move.get_color().lower()[0]
    piece_type = move.piece_moved
    destination_square = move.destination_square
    destination_square_color = get_square_color(destination_square)
    origin_square_color = get_square_color(origin_square)
    origin_square_filename = f'{origin_square_color}_empty.png'
    origin_square_filepath = get_path_to_image(origin_square_filename)
    window[origin_square].update(filename=origin_square_filepath)
    if not move.pawn_promotion_required():
        destination_square_filename = f'{destination_square_color}_{piece_color}{piece_type}.png'
    else:
        destination_square_filename = f'{destination_square_color}_{piece_color}{move.promotion_piece}.png'
    destination_square_filepath = get_path_to_image(destination_square_filename)
    window[destination_square].update(filename=destination_square_filepath)
    if move.castling != 'None':
        rook_home_file = 'h' if move.castling == 'kingside' else 'a'
        back_rank = '1' if piece_color == 'w' else '8'
        rook_destination_file = 'f' if move.castling == 'kingside' else 'd'
        rook_home_square = rook_home_file + back_rank
        rook_home_square_color = get_square_color(rook_home_square)
        rook_home_square_filename = f'{rook_home_square_color}_empty.png'
        rook_home_square_filepath = get_path_to_image(rook_home_square_filename)
        window[rook_home_square].update(filename=rook_home_square_filepath)
        rook_destination_square = rook_destination_file + back_rank
        rook_destination_square_color = get_square_color(rook_destination_square)
        rook_destination_square_filename = f'{rook_destination_square_color}_{piece_color}rook.png'
        rook_destination_square_filepath = get_path_to_image(rook_destination_square_filename)
        window[rook_destination_square].update(filename=rook_destination_square_filepath)
    if move.is_en_passant_capture():
        captured_pawn_rank = '5' if piece_color == 'w' else '4'
        captured_pawn_square = destination_square[0] + captured_pawn_rank
        captured_pawn_square_color = get_square_color(captured_pawn_square)
        captured_pawn_square_filename = f'{captured_pawn_square_color}_empty.png'
        captured_pawn_square_filepath = get_path_to_image(captured_pawn_square_filename)
        window[captured_pawn_square].update(filename=captured_pawn_square_filepath)
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
        side_to_move = position.to_move()
        side_to_move = side_to_move.replace(side_to_move[0], side_to_move[0].upper(), 1)
        layout += [[sg.Text(f"{side_to_move} to move.")]]
    else:
        layout += [[sg.Text('Game is over.')]]
    position_layout = generate_position_layout(position)
    layout += position_layout
    layout += [[sg.Text(output_from_prev_input, key='-TEXT-')]]
    if game_end_text is None:
        to_move = game.current_position.to_move()
        move_number = game.current_position.get_move_number()
        prompt = f'{move_number}'
        if to_move == 'white':
            prompt += '. '
        else:
            prompt += '... '
        layout += [[sg.Text(prompt), sg.InputText(key='-INPUT-', focus=True), sg.Button('Enter move', bind_return_key=True)]]
    else:
        layout += [[sg.Text(game_end_text)]]
    layout += [[sg.Button('Flip board'), sg.Button('Show moves'), sg.Button('Show FEN'), sg.Button('Restart game'), sg.Button('Take back last move')]]
    return layout


def flip_board(game: Game, window: PySimpleGUI.PySimpleGUI.Window, game_end_text: str = None) -> PySimpleGUI.PySimpleGUI.Window:
    game.current_position.flip_position()
    text_value = window['-TEXT-'].DisplayText
    new_layout = generate_layout(game, text_value, game_end_text)
    window.close()
    new_window = sg.Window(TITLE, new_layout, element_padding=(0, 0))
    return new_window


def display_moves(game: Game) -> None:
    moves = game.show_moves(return_string_for_window=True)
    new_window_layout = [[sg.Text(moves)]]
    new_window = sg.Window('Moves', new_window_layout, finalize=True)


def perform_restart(game: Game, window: PySimpleGUI.PySimpleGUI.Window) -> PySimpleGUI.PySimpleGUI.Window:
    game.restart_game()
    new_layout = generate_layout(game, 'Game restarted.')
    window.close()
    new_window = sg.Window(TITLE, new_layout, element_padding=(0, 0))
    return new_window


def perform_takeback(game: Game, window: PySimpleGUI.PySimpleGUI.Window) -> PySimpleGUI.PySimpleGUI.Window:
    takeback_result = game.take_back_last_move(silent=True)
    new_layout = generate_layout(game, takeback_result)
    window.close()
    new_window = sg.Window(TITLE, new_layout, element_padding=(0, 0))
    return new_window


layout = generate_layout(game)
window = sg.Window(TITLE, layout, element_padding=(0, 0))

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    if event == 'Flip board':
        window = flip_board(game, window)
    elif event == 'Show moves':
        display_moves(game)
    elif event == 'Show FEN':
        window['-TEXT-'].update(game.current_position.generate_fen())
    elif event == 'Restart game':
        if sg.popup_yes_no('Are you sure you want to restart?') == 'Yes':
            window = perform_restart(game, window)
    elif event == 'Take back last move':
        window = perform_takeback(game, window)
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
        if game_end_check == 'None':
            update_position_layout_in_window(window, move)
            window['-TEXT-'].update(res)
            window['-INPUT-'].update('')
            # new_layout = generate_layout(game, res)
            # window.close()
            # window = sg.Window(TITLE, new_layout, element_padding=(0, 0))
        else:
            new_layout = generate_layout(game, res, game_end_check)
            window.close()
            window = sg.Window(TITLE, new_layout, element_padding=(0, 0))
            exit_signal = False
            while True:
                event, values = window.read()
                if event == sg.WIN_CLOSED:
                    exit_signal = True
                    break
                elif event == 'Flip board':
                    window = flip_board(game, window, game_end_check)
                elif event == 'Show moves':
                    display_moves(game)
                elif event == 'Show FEN':
                    window['-TEXT-'].update(game.current_position.generate_fen())
                elif event == 'Restart game':
                    if sg.popup_yes_no('Are you sure you want to restart?') == 'Yes':
                        window = perform_restart(game, window)
                        break
                elif event == 'Take back last move':
                    window = perform_takeback(game, window)
                    break
            if exit_signal:
                break


window.close()






