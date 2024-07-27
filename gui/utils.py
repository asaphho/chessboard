from images import IMAGES_FOLDER_PATH
from os import path
from utils.board_functions import square_color_int
from classes.position import Position
import PySimpleGUI as sg
from typing import List


FEN_SYMBOL_TO_PIECE = {'P': 'wpawn', 'K': 'wking', 'Q': 'wqueen', 'B': 'wbishop', 'N': 'wknight', 'R': 'wrook',
                       'p': 'bpawn', 'k': 'bking', 'q': 'bqueen', 'b': 'bbishop', 'n': 'bknight', 'r': 'brook',
                       '1': 'empty'}


def generate_position_layout(position: Position) -> List[List]:
    ranks = '87654321' if not position.is_flipped() else '12345678'
    files = 'abcdefgh'if not position.is_flipped() else 'hgfedcba'
    layout = []
    for r in ranks:
        rank_layout = []
        for f in files:
            curr_square = f'{f}{r}'
            square_color_bit = square_color_int(curr_square)
            square_color = 'light' if square_color_bit == 0 else 'dark'
            piece_at_square = position.look_at_square(curr_square)
            filename = f'{square_color}_{FEN_SYMBOL_TO_PIECE[piece_at_square]}.png'
            filepath = path.join(IMAGES_FOLDER_PATH, filename)
            rank_layout.append(sg.Image(filepath, key=curr_square))
        layout.append(rank_layout)
    return layout
