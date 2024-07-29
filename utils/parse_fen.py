from typing import Dict
from utils.parse_notation import SYMBOL_TO_PIECE

FEN_UPPERCASE_SYMBOL_TO_PIECE = SYMBOL_TO_PIECE.copy()
FEN_UPPERCASE_SYMBOL_TO_PIECE['P'] = 'pawn'


def parse_piece_positions_part(piece_positions_part: str) -> Dict[str, str]:
    """
    Takes in the piece positions part of the FEN (the part with the slashes) and returns a dictionary with all occupied
    squares and the pieces occupying them. Raises ValueError if the following conditions are not all met:
        - There are exactly 8 ranks in the input. Ranks are separated by forward slashes.
        - There are exactly 8 squares accounted for in each of the 8 ranks.
        - Each has side has exactly one king.
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
