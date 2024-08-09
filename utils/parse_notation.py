from typing import Tuple

SYMBOL_TO_PIECE = {'K': 'king', 'Q': 'queen', 'R': 'rook', 'B': 'bishop', 'N': 'knight'}


def piece_to_symbol(piece: str) -> str:
    return piece[0].upper() if piece != 'knight' else 'N'


def find_piece_moved_and_destination_square(move_str: str) -> Tuple[str, str]:
    rank = 0
    file = 'z'
    for i in range(len(move_str) - 1, -1, -1):
        if move_str[i].isnumeric():
            rank = int(move_str[i])
            if i == 0:
                # print('Cannot interpret this move!')
                raise ValueError('Cannot interpret this move!')
            file = move_str[i-1].lower()
            if not file.isalpha():
                # print('Cannot interpret this move!')
                raise ValueError('Cannot interpret this move!')
            break
    if rank == 0 or file == 'z':
        # print('Cannot interpret this move! If castling, use the letter O and not the number 0.')
        raise ValueError('Cannot interpret this move! If castling, use the letter O and not the number 0.')
    if rank > 8 or rank < 1:
        # print(f'Square {file}{rank} does not exist.')
        raise ValueError(f'Square {file}{rank} does not exist.')
    if file not in 'abcdefgh':
        # print(f'Square {file}{rank} does not exist.')
        raise ValueError(f'Square {file}{rank} does not exist.')
    destination_square = f'{file}{rank}'
    move_str_bef_destination_square = move_str.rsplit(destination_square, maxsplit=1)[0]
    if move_str_bef_destination_square == '':
        piece_moved = 'P'
    else:
        first_char = move_str_bef_destination_square[0]
        if first_char in ('Q', 'R', 'B', 'N', 'K'):
            piece_moved = first_char
        elif first_char in 'abcdefgh':
            piece_moved = 'P'
        else:
            # print(f'Unrecognized piece symbol {first_char}. Non-pawn piece symbols must be given in uppercase. Allowed piece symbols: K, Q, R, B, N')
            raise ValueError(f'Unrecognized piece symbol {first_char}. Non-pawn piece symbols must be given in uppercase. Allowed piece symbols: K, Q, R, B, N')
    return piece_moved, destination_square


def check_for_castling(move_str: str) -> str:
    if move_str.replace(' ', '').upper().startswith('O-O-O'):
        return 'q'
    elif move_str.replace(' ', '').upper().startswith('O-O'):
        return 'k'
    else:
        return 'N'


def check_for_disambiguating_string(move_str: str, destination_square: str, piece_symbol: str) -> str:
    piece_symbol_stripped = move_str.lstrip(piece_symbol)
    bef_destination_square = piece_symbol_stripped.rsplit(destination_square, maxsplit=1)[0]
    disambiguation_string = bef_destination_square.rstrip('x')
    if len(disambiguation_string) == 1 and disambiguation_string in 'abcdefgh':
        return disambiguation_string
    elif len(disambiguation_string) == 1 and disambiguation_string in '12345678':
        return disambiguation_string
    elif len(disambiguation_string) == 2 and disambiguation_string[0] in 'abcdefgh' and disambiguation_string[1] in '12345678':
        return disambiguation_string
    elif disambiguation_string == '':
        return disambiguation_string
    else:
        # print(f'Could not recognize {disambiguation_string} as a disambiguation string.')
        raise ValueError(f'Could not recognize {disambiguation_string} as a disambiguation string.')


def check_for_promotion_piece(move_str: str, destination_square: str) -> str:
    str_after_destination_square = move_str.rsplit(destination_square, maxsplit=1)[1].lstrip('=')
    if str_after_destination_square == '':
        return 'None'
    elif str_after_destination_square[0] in ('Q', 'R', 'B', 'N'):
        return str_after_destination_square[0]
    else:
        # print(f'Could not recognize {str_after_destination_square[0]} as a promotion piece symbol. Must be given in uppercase. Allowed symbols: Q, R, B, N')
        raise ValueError(f'Could not recognize {str_after_destination_square[0]} as a promotion piece symbol. Must be given in uppercase. Allowed symbols: Q, R, B, N')


def pawn_capture_origin_file(move_str: str, destination_square: str) -> str:
    str_bef_destination_square = move_str.rsplit(destination_square, maxsplit=1)[0]
    if str_bef_destination_square == '':
        return ''
    first_char = str_bef_destination_square[0]
    valid_file_captures = {'a': ('b',), 'b': ('a', 'c'), 'c': ('b', 'd'), 'd': ('c', 'e'),
                           'e': ('d', 'f'), 'f': ('e', 'g'), 'g': ('f', 'h'), 'h': ('g',)}
    destination_file = destination_square[0]
    if first_char not in valid_file_captures:
        # print('Could not interpret this move! If you are using uppercase for a file from which a pawn captures from, use lowercase instead.')
        raise ValueError('Could not interpret this move! If you are using uppercase for a file from which a pawn captures from, use lowercase instead.')
    elif destination_file not in valid_file_captures[first_char]:
        # print(f'Pawn cannot capture from {first_char}-file to {destination_file}-file!')
        raise ValueError(f'Pawn cannot capture from {first_char}-file to {destination_file}-file!')
    else:
        return first_char
