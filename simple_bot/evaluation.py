from typing import List, Set, Iterable

from classes.move import LegalMove
from classes.position import Position, opposite_color
from simple_bot.parameters import MATERIAL_DICT


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


def squares_controlled_by_pawns(position: Position, color: str) -> Set[str]:
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
    return set(squares_attacked)


def piece_moves_reduced_by_enemy_pawn_control(unreduced_piece_moves: List[LegalMove],
                                              squares_controlled: Iterable[str]) -> List[LegalMove]:
    """
    Returns the subset of unreduced_piece_moves that do not put a piece on a square controlled by an enemy pawn
    (pins are ignored).
    :param unreduced_piece_moves: The legal piece moves (knight, bishop, rook, queen) in the current position of one
    side
    :param squares_controlled: An iterable containing all the squares attacked by enemy pawns in the same position
    :return:
    """
    return [move for move in unreduced_piece_moves if move.destination_square not in squares_controlled]