from typing import List, Iterable
from utils.board_functions import scan_qbr_scope, scan_kn_scope, get_intervening_squares
from classes.move import LegalMove
from classes.position import Position, opposite_color
from simple_bot.parameters import (MATERIAL_DICT, WHITE_PAWN_CONTROL_SCORES, BLACK_PAWN_CONTROL_SCORES,
                                   ACTIVITY_COUNT_MULTIPLIER, CHECKMATE_SCORE)
from simple_bot.utils import branch_from_position

SYMBOL_TO_PIECE = {'P': 'pawn', 'K': 'king', 'Q': 'queen', 'R': 'rook', 'B': 'bishop', 'N': 'knight'}


def count_material(position: Position, color: str) -> int:
    """
    Counts the number of pawns worth of material on the given side in the given position
    :param position:
    :param color: 'white' or 'black'
    :return:
    """
    pieces = position.get_pieces_by_color(color)
    piece_types = pieces.list_unique_piece_types()
    total = 0
    for piece_type in piece_types:
        number_of_pieces_of_type = len(pieces.get_piece_type_squares(piece_type))
        total += number_of_pieces_of_type * MATERIAL_DICT[piece_type]
    return total


def count_material_imbalance(position: Position, color: str) -> int:
    """
    Calculates the material imbalance in favor of the given color in the given position.
    :param position:
    :param color: 'white' or 'black'.
    :return: e.g. returning 3 if color='white' means that white is up 3 pawns of material
    """
    own_material = count_material(position, color)
    opponents_material = count_material(position, opposite_color(color))
    return own_material - opponents_material


def evaluate_exchange_square(position: Position, square: str, init_possible_captures: List[LegalMove]) -> int:
    """
    Counts the amount of material that the side to move stands to gain from initiating a series of captures and
    recaptures on the given square. Both sides "dogpile" onto the square, sending their least valuable pieces to capture
    first, until one side cannot recapture.
    :param init_possible_captures:
    :param square:
    :param position:
    :return:
    """
    capturing_move = min(init_possible_captures, key=lambda x: MATERIAL_DICT[x.piece_moved])
    if not capturing_move.is_en_passant_capture():
        captured_piece = SYMBOL_TO_PIECE[position.look_at_square(square).upper()]
    else:
        captured_piece = 'pawn'
    position_after_capture = branch_from_position(position, capturing_move)
    possible_recaptures = [move for move in position_after_capture.get_all_legal_moves_for_side_to_move() if move.destination_square == square and move.is_capture()]
    material_gain = MATERIAL_DICT[captured_piece]
    if not possible_recaptures:
        return material_gain
    else:
        return material_gain - evaluate_exchange_square(position_after_capture, square, possible_recaptures)


def all_legal_piece_moves(position: Position, color: str) -> List[LegalMove]:
    """
    Returns all the legal piece moves (knight, bishop, rook, or queen) in the given position with the given color to
    move
    :param position:
    :param color: 'white' or 'black'
    :return:
    """
    all_legal_moves = position.get_all_legal_moves_for_color(color)
    legal_piece_moves = [move for move in all_legal_moves if move.piece_moved in ('rook', 'queen', 'bishop', 'knight')]
    return legal_piece_moves


def piece_activity(position: Position, color: str) -> List[str]:
    squares = []
    own_pieces = position.get_pieces_by_color(color)
    occupied_squares = position.get_occupied_squares()
    for piece_type in own_pieces.list_unique_piece_types():
        if piece_type in ('queen', 'bishop', 'rook'):
            for from_square in own_pieces.get_piece_type_squares(piece_type):
                scope = scan_qbr_scope(piece_type, from_square)
                for line_type in scope:
                    for candidate_square in scope[line_type]:
                        intervening_squares = get_intervening_squares(from_square, candidate_square, line_type)
                        blocked = any([sq in occupied_squares for sq in intervening_squares])
                        if not blocked:
                            squares.append(candidate_square)
        elif piece_type == 'knight':
            for from_square in own_pieces.get_piece_type_squares(piece_type):
                scope = scan_kn_scope(piece_type, from_square)
                for sq in scope:
                    if sq not in own_pieces.get_occupied_squares():
                        squares.append(sq)
    return squares


def squares_controlled_by_pawns(position: Position, color: str) -> List[str]:
    """
    Returns all the squares attacked by pawns (ignoring any pins) by the given color in the given position.
    :param position:
    :param color: 'white' or 'black'
    :return: the set of all squares attacked by white pawns if color='white'. Pins are ignored.
    """
    squares_attacked = []
    squares_with_pawns = position.get_pieces_by_color(color).get_piece_type_squares('pawn')
    for square in squares_with_pawns:
        squares_attacked.extend(position.scan_pawn_attacked_squares(color, square))
    return squares_attacked


def get_pawn_control_score(controlled_squares: List[str], color: str) -> float:
    """
    Gets the score of the given color in a position from the squares it attacks by its pawns.
    :param controlled_squares: The output of squares_controlled_by_pawns
    :param color: 'white' or 'black'
    :return: the total score
    """
    total = 0
    for sq in controlled_squares:
        total += WHITE_PAWN_CONTROL_SCORES[sq] if color == 'white' else BLACK_PAWN_CONTROL_SCORES[sq]
    return total


def piece_moves_reduced_by_enemy_pawn_control(unreduced_piece_moves: List[str],
                                              squares_controlled: Iterable[str]) -> List[str]:
    """
    Returns the subset of unreduced_piece_moves that do not put a piece on a square controlled by an enemy pawn
    (pins are ignored).
    :param unreduced_piece_moves: The piece moves (knight, bishop, rook, queen) in the current position of one
    side
    :param squares_controlled: An iterable containing all the squares attacked by enemy pawns in the same position
    :return:
    """
    return [sq for sq in unreduced_piece_moves if sq not in squares_controlled]


def evaluate(position: Position) -> float:
    """
    The evaluation function to be called to evaluate how good or bad a position is for the side that has just moved.
    :param position: Position object
    :return: float. The higher, the better. 0 means equal position.
    """
    side_to_move = position.to_move()
    side_evaluating_for = opposite_color(side_to_move)
    if not position.get_all_legal_moves_for_color(side_to_move):
        if position.is_under_check(side_to_move):
            return CHECKMATE_SCORE
        else:
            return 0
    score = count_material_imbalance(position, side_evaluating_for)  # MATERIAL IMBALANCE
    own_pawn_controlled_squares = squares_controlled_by_pawns(position, side_evaluating_for)
    opposing_pawn_controlled_squares = squares_controlled_by_pawns(position, side_to_move)
    activity = piece_activity(position, side_evaluating_for)
    opposing_activity = piece_activity(position, side_to_move)
    piece_moves_reduced = piece_moves_reduced_by_enemy_pawn_control(activity, opposing_pawn_controlled_squares)
    opposing_piece_moves_reduced = piece_moves_reduced_by_enemy_pawn_control(opposing_activity,
                                                                             own_pawn_controlled_squares)
    score += ACTIVITY_COUNT_MULTIPLIER * (len(piece_moves_reduced) - len(opposing_piece_moves_reduced))  # LEGAL PIECE MOVES
    score += get_pawn_control_score(own_pawn_controlled_squares, side_evaluating_for) - get_pawn_control_score(opposing_pawn_controlled_squares, side_to_move)  # SQUARES CONTROLLED BY PAWNS
    return score
