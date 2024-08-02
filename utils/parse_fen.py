from typing import Dict, List

from classes.position import Position, ColorPosition, opposite_color
from utils.parse_notation import SYMBOL_TO_PIECE

FEN_UPPERCASE_SYMBOL_TO_PIECE = SYMBOL_TO_PIECE.copy()
FEN_UPPERCASE_SYMBOL_TO_PIECE['P'] = 'pawn'


def parse_piece_positions_part(piece_positions_part: str) -> Dict[str, str]:
    """
    Takes in the piece positions part of the FEN (the part with the slashes) and returns a dictionary with all occupied
    squares and the pieces occupying them. Raises ValueError if the following conditions are not all met:
        - There are exactly 8 ranks in the input. Ranks are separated by forward slashes.
        - There are exactly 8 squares accounted for in each of the 8 ranks.
        - Each side has exactly one king.
        - No pawns are on either of the extreme ranks.
        DOES NOT CHECK WHETHER BOTH KINGS ARE UNDER CHECK OR NOT. Does not check for other impossible positions,
        e.g. One side having more than 8 pawns, white pawns on a2, a3, and b2, etc.
    :param piece_positions_part: e.g. 'rnbqk2r/ppp1bppp/4pn2/3p2B1/2PP4/2N5/PP2PPPP/R2QKBNR'
    :return: a dictionary of the following form {'a2': 'P', 'e1': 'K', 'e6': 'k', 'h1': 'R', 'f6': 'n'}. Uppercase indicates a white piece, lowercase a black piece.
    """
    if (black_king_count := piece_positions_part.count('k')) != 1:
        raise ValueError(f'Black has {black_king_count} kings.')
    if (white_king_count := piece_positions_part.count('K')) != 1:
        raise ValueError(f'White has {white_king_count} kings.')
    fen_rank_strings = [rank_str.strip() for rank_str in piece_positions_part.split('/')]
    if (number_of_ranks := len(fen_rank_strings)) != 8:
        raise ValueError(f'Incorrect number of ranks. Expected 8, given {number_of_ranks}. Ranks read: {fen_rank_strings}.')
    if any(['p' in rank for rank in (fen_rank_strings[0].lower(), fen_rank_strings[-1].lower())]):
        raise ValueError('Pawns found on extreme ranks.')
    ranks = '87654321'
    files = 'abcdefgh'
    square_piece_dict = {}
    for i in range(8):
        curr_rank = ranks[i]
        curr_fen_rank_str = fen_rank_strings[i]
        if curr_fen_rank_str == '':
            raise ValueError(f'Rank {curr_rank} is empty.')
        total_squares_in_rank = 0
        curr_file_index = 0
        curr_fen_rank_str_index = 0
        while curr_file_index <= 7:
            try:
                char_read = curr_fen_rank_str[curr_fen_rank_str_index]
            except IndexError:
                raise ValueError(f'Not enough squares accounted for in rank {curr_rank}: "{curr_fen_rank_str}". Only {total_squares_in_rank} squares accounted for.')
            if char_read.isnumeric():
                total_squares_in_rank += int(char_read)
                curr_file_index += int(char_read)
                if total_squares_in_rank > 8:
                    raise ValueError(f'Too many squares in rank {curr_rank}: "{curr_fen_rank_str}". There should be only 8 squares per rank.')
            elif char_read.isalpha():
                if char_read.upper() not in FEN_UPPERCASE_SYMBOL_TO_PIECE:
                    raise ValueError(f'Unrecognized piece symbol: {char_read}.')
                curr_file = files[curr_file_index]
                curr_square = f'{curr_file}{curr_rank}'
                square_piece_dict[curr_square] = char_read
                curr_file_index += 1
                total_squares_in_rank += 1
            else:
                raise ValueError(f'Invalid symbol: {char_read}.')
            curr_fen_rank_str_index += 1
        if curr_fen_rank_str_index <= len(curr_fen_rank_str) - 1:
            raise ValueError(f'Too many squares in rank {curr_rank}: {curr_fen_rank_str}.')
    return square_piece_dict


def make_virtual_position(square_piece_dict: Dict[str, str], side_to_move: str) -> Position:
    """
    Makes a Position object to evaluate whether it is valid.
    :param square_piece_dict: the output of parse_piece_positions_part
    :param side_to_move: 'white' or 'black'
    :return:
    """
    white_pieces = {}
    black_pieces = {}
    for square in square_piece_dict:
        fen_symbol = square_piece_dict[square]
        piece = FEN_UPPERCASE_SYMBOL_TO_PIECE[fen_symbol.upper()]
        if fen_symbol.isupper():
            if piece not in white_pieces:
                white_pieces[piece] = [square]
            else:
                white_pieces[piece].append(square)
        else:
            if piece not in black_pieces:
                black_pieces[piece] = [square]
            else:
                black_pieces[piece].append(square)
    white_position = ColorPosition('white', white_pieces)
    black_position = ColorPosition('black', black_pieces)
    return Position(white_pieces=white_position, black_pieces=black_position, side_to_move=side_to_move)


def evaluate_virtual_position(virtual_position: Position) -> None:
    """
    Raises an AssertionError if the side not to move is under check in this position.
    :param virtual_position:
    :return:
    """
    side_not_to_move = opposite_color(virtual_position.to_move())
    assert not virtual_position.is_under_check(side_not_to_move)


def scan_possible_castling_potential(virtual_position: Position) -> Dict[str, List[str]]:
    """
    Checks if the kings and rooks are still on their home squares to determine if castling potential is still possible
    :param virtual_position:
    :return: a dictionary of the following form: {'white': ['kingside', 'queenside'], 'black': ['kingside']}. If one side cannot castle, the value will be an empty list. e.g. {'white': [], 'black': ['kingside']}
    """
    possible_castling_potential = {'white': [], 'black': []}
    for color in possible_castling_potential:
        pieces = virtual_position.get_pieces_by_color(color)
        back_rank = '1' if color == 'white' else '8'
        king_on_home_square = pieces.get_king_square() == f'e{back_rank}'
        has_rooks = 'rook' in pieces.list_unique_piece_types()
        if king_on_home_square and has_rooks:
            rook_squares = pieces.get_piece_type_squares('rook')
            for square in rook_squares:
                if square == f'a{back_rank}':
                    possible_castling_potential[color].append('queenside')
                elif square == f'h{back_rank}':
                    possible_castling_potential[color].append('kingside')
    return possible_castling_potential


def list_possible_en_passant_squares(virtual_position: Position) -> List[str]:
    """
    Looks for pawns on the side not to move that could possibly have used their two-square move immediately before this
    position. Lists the en passant target squares for all such pawns.
    :param virtual_position:
    :return:
    """
    side_not_to_move = opposite_color(virtual_position.to_move())
    if 'pawn' not in virtual_position.get_pieces_by_color(side_not_to_move).list_unique_piece_types():
        return []
    two_square_move_rank = '4' if side_not_to_move == 'white' else '5'
    ranks_to_be_empty = ['2', '3'] if side_not_to_move == 'white' else ['7', '6']
    pawn_squares = virtual_position.get_pieces_by_color(side_not_to_move).get_piece_type_squares('pawn')
    possible_en_passant_squares = []
    squares_on_correct_rank = [square for square in pawn_squares if square[1] == two_square_move_rank]
    if len(squares_on_correct_rank) == 0:
        return []
    occupied_squares = virtual_position.get_occupied_squares()
    for square in squares_on_correct_rank:
        file = square[0]
        if all([sq not in occupied_squares for sq in [f'{file}{rank}' for rank in ranks_to_be_empty]]):
            possible_en_passant_squares.append(f'{file}{ranks_to_be_empty[1]}')
    return possible_en_passant_squares


def parse_full_fen(full_fen: str) -> Position:
    fen_parts = [part.strip() for part in full_fen.split(' ') if part.strip() != '']
    try:
        piece_position_part = fen_parts[0]
    except IndexError:
        raise ValueError('Input empty')
    try:
        square_piece_dict = parse_piece_positions_part(piece_position_part)
    except ValueError as e:
        raise ValueError(str(e))
    try:
        active_side_symbol = fen_parts[1]
    except IndexError:
        raise ValueError('No active side')
    if active_side_symbol.lower() == 'w':
        side_to_move = 'white'
    elif active_side_symbol.lower() == 'b':
        side_to_move = 'black'
    else:
        raise ValueError(f'Could not recognise {active_side_symbol} as active side. Must be \'w\' or \'b\'.')
    virtual_position = make_virtual_position(square_piece_dict, side_to_move)
    try:
        evaluate_virtual_position(virtual_position)
    except AssertionError:
        raise ValueError('Side not to move is under check. Position is illegal.')

