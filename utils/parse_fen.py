from typing import Dict, List

from classes.position import Position, ColorPosition, opposite_color
from utils.parse_notation import SYMBOL_TO_PIECE

FEN_UPPERCASE_SYMBOL_TO_PIECE = SYMBOL_TO_PIECE.copy()
FEN_UPPERCASE_SYMBOL_TO_PIECE['P'] = 'pawn'


def parse_piece_positions_part(piece_positions_part: str) -> Dict[str, str]:
    """
    Parses the piece placement portion of a FEN string and returns a mapping of squares to piece symbols.

    Validates the following and ONLY the following:
    - Exactly 8 ranks present, separated by slashes.
    - Each rank has exactly 8 squares accounted for.
    - Exactly one king for each side.
    - No pawns are on the first or last rank.

    Args:
        piece_positions_part (str): The piece placement section of a FEN string
            (e.g., 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR').

    Returns:
        Dict[str, str]: A mapping of square strings to piece symbols (e.g., {'e1': 'K', 'a7': 'p'}).

    Raises:
        ValueError: If the FEN piece layout is structurally or logically invalid.
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
    Constructs a Position object using square-to-piece mappings and side to move.

    Args:
        square_piece_dict (Dict[str, str]): Output from `parse_piece_positions_part`.
        side_to_move (str): Either 'w' or 'b', indicating which side is to move.

    Returns:
        Position: A Position object containing the board state (without full validation).
    """
    white_pieces = {}
    black_pieces = {}
    for square in square_piece_dict:
        fen_symbol = square_piece_dict[square]
        piece = fen_symbol.upper()
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
    white_position = ColorPosition('w', white_pieces)
    black_position = ColorPosition('b', black_pieces)
    return Position(white_pieces=white_position, black_pieces=black_position, side_to_move=side_to_move)


def evaluate_virtual_position(virtual_position: Position) -> None:
    """
    Checks that the side *not* to move is not under check in the given position.

    Used to validate legality of FENs: a legal position cannot start with the
    non-moving side in check.

    Args:
        virtual_position (Position): The position to evaluate.

    Raises:
        AssertionError: If the side not to move is in check.
    """
    side_not_to_move = opposite_color(virtual_position.to_move())
    assert not virtual_position.is_under_check(side_not_to_move)


def scan_possible_castling_potential(virtual_position: Position) -> Dict[str, List[str]]:
    """
    Identifies potential castling rights based solely on king and rook positions.

    Does not verify check conditions or intervening pieces — only checks
    whether the relevant pieces are still on their home squares.

    Args:
        virtual_position (Position): The position to evaluate.

    Returns:
        Dict[str, List[str]]: A dictionary like {'w': ['k', 'q'], 'b': ['k']}, where each value is
        a list of castling sides that could be legal if no other rules are violated.
    """
    possible_castling_potential = {'w': [], 'b': []}
    for color in possible_castling_potential:
        pieces = virtual_position.get_pieces_by_color(color)
        back_rank = '1' if color == 'w' else '8'
        king_on_home_square = pieces.get_king_square() == f'e{back_rank}'
        has_rooks = 'R' in pieces.list_unique_piece_types()
        if king_on_home_square and has_rooks:
            rook_squares = pieces.get_piece_type_squares('R')
            for square in rook_squares:
                if square == f'a{back_rank}':
                    possible_castling_potential[color].append('q')
                elif square == f'h{back_rank}':
                    possible_castling_potential[color].append('k')
    return possible_castling_potential


def list_possible_en_passant_squares(virtual_position: Position) -> List[str]:
    """
    Lists all possible en passant target squares based on the last move having been a two-square pawn advance.

    Only considers pawns on the fourth or fifth ranks (depending on side) and checks
    that the intermediate squares are unoccupied.

    Args:
        virtual_position (Position): The position to evaluate.

    Returns:
        List[str]: A list of valid en passant target squares (e.g., ['e3']).
    """
    side_not_to_move = opposite_color(virtual_position.to_move())
    if 'P' not in virtual_position.get_pieces_by_color(side_not_to_move).list_unique_piece_types():
        return []
    two_square_move_rank = '4' if side_not_to_move == 'w' else '5'
    ranks_to_be_empty = ['2', '3'] if side_not_to_move == 'w' else ['7', '6']
    pawn_squares = virtual_position.get_pieces_by_color(side_not_to_move).get_piece_type_squares('P')
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
    """
        Parses a full FEN string into a validated `Position` object.

        This function performs full validation of the FEN format:
        - Parses piece layout, side to move, castling rights, en passant square, half-move clock, and move number.
        - Validates king count, pawn legality, and basic structural correctness.
        - Rejects illegal positions (e.g., side not to move is in check).

        Args:
            full_fen (str): A complete FEN string.

        Returns:
            Position: A fully constructed and validated game state.

        Raises:
            ValueError: If the FEN is malformed or represents an illegal position.
        """
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
        side_to_move = 'w'
    elif active_side_symbol.lower() == 'b':
        side_to_move = 'b'
    else:
        raise ValueError(f'Could not recognise {active_side_symbol} as active side. Must be \'w\' or \'b\'.')
    virtual_position = make_virtual_position(square_piece_dict, side_to_move)
    try:
        evaluate_virtual_position(virtual_position)
    except AssertionError:
        raise ValueError('Side not to move is under check. Position is illegal.')
    try:
        castling_rights = fen_parts[2]
    except IndexError:
        raise ValueError('No castling rights indicated.')
    castling_potential = scan_possible_castling_potential(virtual_position)
    if 'K' in castling_rights:
        if 'k' not in castling_potential['w']:
            castling_rights = castling_rights.replace('K', '')
    if 'k' in castling_rights:
        if 'k' not in castling_potential['b']:
            castling_rights = castling_rights.replace('k', '')
    if 'Q' in castling_rights:
        if 'q' not in castling_potential['w']:
            castling_rights = castling_rights.replace('Q', '')
    if 'q' in castling_rights:
        if 'q' not in castling_potential['b']:
            castling_rights = castling_rights.replace('q', '')
    if 'K' not in castling_rights:
        virtual_position.white_pieces.disable_short_castling()
    if 'k' not in castling_rights:
        virtual_position.black_pieces.disable_short_castling()
    if 'Q' not in castling_rights:
        virtual_position.white_pieces.disable_long_castling()
    if 'q' not in castling_rights:
        virtual_position.black_pieces.disable_long_castling()
    virtual_position.virtual_white_pieces = virtual_position.white_pieces.copy()
    virtual_position.virtual_black_pieces = virtual_position.black_pieces.copy()
    try:
        en_passant_square = fen_parts[3]
    except IndexError:
        raise ValueError('No en passant square')
    possible_en_passant_squares = list_possible_en_passant_squares(virtual_position)
    if (en_passant_square not in possible_en_passant_squares) and (en_passant_square != '-'):
        raise ValueError(f'Invalid en passant square {en_passant_square}.')
    if en_passant_square != '-':
        virtual_position.set_en_passant_square(en_passant_square)
    try:
        half_move_clock = fen_parts[4]
    except IndexError:
        raise ValueError('No half-move clock indicated.')
    if not half_move_clock.isnumeric():
        raise ValueError('Half-move clock must be numeric.')
    half_move_clock = int(half_move_clock)
    if half_move_clock > 100 or half_move_clock < 0:
        raise ValueError('Half-move clock must be non-negative and no greater than 100.')
    virtual_position.set_half_move_clock(half_move_clock)
    try:
        move_number_part = fen_parts[5]
    except IndexError:
        raise ValueError('No move number')
    if not move_number_part.isnumeric():
        raise ValueError('Move number must be numeric.')
    move_number = int(move_number_part)
    if move_number < 1:
        raise ValueError('Move number must be no smaller than 1.')
    virtual_position.set_move_number(move_number)
    return virtual_position
