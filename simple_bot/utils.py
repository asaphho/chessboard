from classes.position import Position
from classes.move import LegalMove


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

