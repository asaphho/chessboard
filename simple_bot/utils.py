from classes.position import Position, opposite_color
from classes.move import LegalMove
from typing import Union

MATERIAL_DICT = {'king': 0, 'pawn': 1, 'knight': 3, 'bishop': 3, 'rook': 5, 'queen': 9}


def branch_from_position(position: Position, move: LegalMove) -> Position:
    new_position = position.copy()
    new_position.process_legal_move(move)
    return new_position


def check_if_move_ends_game(current_position: Position, move: LegalMove) -> str:
    """
    Only checks if move ends the game by checkmate or stalemate. Does not check if game will end by repetition or by
    50-move draw or by reduction as a result of this move.
    :param current_position:
    :param move:
    :return: 'checkmate' if move delivers checkmate, 'stalemate' if move delivers stalemate, 'None' if move does neither
    """
    new_position = branch_from_position(current_position, move)
    to_move = new_position.to_move()
    possible_legal_moves = new_position.get_all_legal_moves_for_color(to_move)
    if len(possible_legal_moves) >= 1:
        return 'None'
    if new_position.is_under_check(to_move):
        return 'checkmate'
    return 'stalemate'


def look_for_mate_in_one(current_position: Position) -> Union[LegalMove, None]:
    """
    Looks for a mate in one in the current position for the current side to move.
    :param current_position:
    :return: a LegalMove object that delivers checkmate when played in the current position, or None if no mate exists.
    """
    all_legal_moves = current_position.get_all_legal_moves_for_color(current_position.to_move())
    for move in all_legal_moves:
        if check_if_move_ends_game(current_position, move) == 'checkmate':
            return move
    return None


def move_allows_mate_in_one(current_position: Position, move: LegalMove) -> bool:
    """
    Checks if the LegalMove played in the current position will allow a mate in one as an immediate reply.
    :param current_position:
    :param move:
    :return: True if it allows a mate in one. False if not.
    """
    new_position = branch_from_position(current_position, move)
    mating_move = look_for_mate_in_one(new_position)
    return mating_move is not None


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


