import PySimpleGUI as sg
from classes.game import Game
from typing import List
from gui.utils import generate_position_layout

intro_text = ('Enter moves in standard algebraic notation. Always use uppercase for non-pawn pieces.\n '
              'Give all files in lowercase. Do not include any spaces.\n ')
# buttons: 'Flip board' 'Show moves' 'Show FEN' 'Restart game' 'Take back last move'
game = Game()


def generate_layout(game, output_from_prev_input: str = '') -> List[List]:
    position = game.current_position
    layout = [[sg.Text(intro_text)]]
    position_layout = generate_position_layout(position)
    layout += position_layout + [[sg.Text(output_from_prev_input, key='-TEXT-')]]
    to_move = game.current_position.to_move()
    move_number = game.current_position.get_move_number()
    prompt = f'{move_number}'
    if to_move == 'white':
        prompt += '. '
    else:
        prompt += '... '
    layout += [[sg.Text(prompt), sg.InputText(key='-INPUT-'), sg.Button('Enter move')]]
    layout += [[sg.Button('Flip board'), sg.Button('Show moves'), sg.Button('Show FEN'), sg.Button('Restart game'), sg.Button('Take back last move')]]
    return layout


layout = generate_layout(game)
window = sg.Window('Title', layout, element_padding=(0, 0))

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    if event == 'Flip board':
        game.current_position.flip_position()
        text_value = window['-TEXT-'].DisplayText
        new_layout = generate_layout(game, text_value)
        window.close()
        window = sg.Window('Title', new_layout, element_padding=(0, 0))
    elif event == 'Show moves':
        moves = game.show_moves(return_string_for_window=True)
        new_window_layout = [[sg.Text(moves)]]
        new_window = sg.Window('Moves', new_window_layout, finalize=True)
    elif event == 'Show FEN':
        window['-TEXT-'].update(game.current_position.generate_fen())

window.close()
