import PySimpleGUI as sg
import PySimpleGUI.PySimpleGUI
from version import software_version
from classes.game import Game
from typing import List
from gui.utils import generate_position_layout

TITLE = f'chessboard v{software_version}'

intro_text = ('Enter moves in standard algebraic notation. Always use uppercase for non-pawn pieces.\n '
              'Give all files in lowercase. Do not include any spaces.\n ')
# buttons: 'Flip board' 'Show moves' 'Show FEN' 'Restart game' 'Take back last move'
game = Game()


def generate_layout(game: Game, output_from_prev_input: str = '', game_end_text: str = None) -> List[List]:
    position = game.current_position
    layout = [[sg.Text(intro_text)]]
    side_to_move = position.to_move()
    side_to_move = side_to_move.replace(side_to_move[0], side_to_move[0].upper(), 1)
    layout += [[sg.Text(f"{side_to_move} to move.")]]
    position_layout = generate_position_layout(position)
    layout += position_layout + [[sg.Text(output_from_prev_input, key='-TEXT-')]]
    to_move = game.current_position.to_move()
    move_number = game.current_position.get_move_number()
    prompt = f'{move_number}'
    if to_move == 'white':
        prompt += '. '
    else:
        prompt += '... '
    if game_end_text is None:
        layout += [[sg.Text(prompt), sg.InputText(key='-INPUT-'), sg.Button('Enter move')]]
    else:
        layout += [[sg.Text(game_end_text)]]
    layout += [[sg.Button('Flip board'), sg.Button('Show moves'), sg.Button('Show FEN'), sg.Button('Restart game'), sg.Button('Take back last move')]]
    return layout


layout = generate_layout(game)
window = sg.Window(TITLE, layout, element_padding=(0, 0))


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
            res = game.process_input_notation(input_notation)
        except Exception as e:
            window['-TEXT-'].update(str(e))
            continue
        game_end_check = game.check_game_end_conditions()
        if game_end_check == 'None':
            new_layout = generate_layout(game, res)
            window.close()
            window = sg.Window(TITLE, new_layout, element_padding=(0, 0))
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
