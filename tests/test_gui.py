import PySimpleGUI as sg
from classes.position import generate_starting_position
from classes.move import LegalMove
from gui.utils import generate_position_layout

position = generate_starting_position()
position.process_legal_move(LegalMove(color='white', piece_type='pawn', origin_square='d2', destination_square='d4'))
position.process_legal_move(LegalMove(color='black', piece_type='pawn', origin_square='e7', destination_square='e5'))
position.process_legal_move(LegalMove(color='white', piece_type='pawn', origin_square='d4', destination_square='e5', is_capture=True))
position.process_legal_move(LegalMove(color='black', piece_type='queen', origin_square='d8', destination_square='e7'))
position.process_legal_move(LegalMove(color='white', piece_type='bishop', origin_square='c1', destination_square='f4'))
position.process_legal_move(LegalMove(color='black', piece_type='queen', origin_square='e7', destination_square='b4'))
position.process_legal_move(LegalMove(color='white', piece_type='bishop', origin_square='f4', destination_square='d2'))
position.process_legal_move(LegalMove(color='black', piece_type='queen', origin_square='b4', destination_square='b2', is_capture=True))
position.process_legal_move(LegalMove(color='white', piece_type='bishop', origin_square='d2', destination_square='c3'))
position.process_legal_move(LegalMove(color='black', piece_type='bishop', origin_square='f8', destination_square='b4'))
position.process_legal_move(LegalMove(color='white', piece_type='queen', origin_square='d1', destination_square='d2'))
position.process_legal_move(LegalMove(color='black', piece_type='bishop', origin_square='b4', destination_square='c3', is_capture=True))
position.process_legal_move(LegalMove(color='white', piece_type='queen', origin_square='d2', destination_square='c3', is_capture=True))
position.process_legal_move(LegalMove(color='black', piece_type='queen', origin_square='b2', destination_square='c1'))
position_layout = generate_position_layout(position)
layout = position_layout + [[sg.Text(position.generate_fen())]]
layout += [[sg.Button('Flip board')]]
window = sg.Window('Title', layout, element_padding=(0, 0))

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    if event == 'Flip board':
        position.flip_position()
        print(position.is_flipped())
        position_layout = generate_position_layout(position)
        layout = position_layout + [[sg.Text(position.generate_fen())]]
        layout += [[sg.Button('Flip board')]]
        window.close()
        window = sg.Window('Title', layout, element_padding=(0, 0))

window.close()
