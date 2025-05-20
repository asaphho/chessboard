from classes.position import Position
from classes.move import LegalMove
from typing import Union


def branch_from_position(position: Position, move: LegalMove) -> Position:
    """
        Creates a new Position object by applying a legal move to a copy of the given position.

        Args:
            position (Position): The current position.
            move (LegalMove): The move to apply.

        Returns:
            Position: A new position reflecting the game state after the move.
        """
    new_position = position.copy()
    new_position.process_legal_move(move)
    return new_position


def check_if_move_ends_game(current_position: Position, move: LegalMove) -> str:
    """
    Determines whether a legal move ends the game by checkmate or stalemate.

    Does not consider repetition, 50-move rule, or insufficient material.

    Args:
        current_position (Position): The current game state.
        move (LegalMove): The legal move to evaluate.

    Returns:
        str:
            - 'checkmate' if the move delivers checkmate.
            - 'stalemate' if the move results in stalemate.
            - 'None' if the move does not end the game in either way.
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
    Searches for a move that results in checkmate in one ply from the current position.

    Args:
        current_position (Position): The current game state.

    Returns:
        LegalMove | None: A legal move that delivers checkmate, or None if no such move exists.
    """
    all_legal_moves = current_position.get_all_legal_moves_for_color(current_position.to_move())
    for move in all_legal_moves:
        if check_if_move_ends_game(current_position, move) == 'checkmate':
            return move
    return None


def move_allows_mate_in_one(current_position: Position, move: LegalMove) -> bool:
    """
    Determines whether playing a given legal move allows the opponent to deliver a mate in one.

    Args:
        current_position (Position): The current game state.
        move (LegalMove): The move to evaluate.

    Returns:
        bool: True if the move allows a mate-in-one by the opponent, False otherwise.
    """
    new_position = branch_from_position(current_position, move)
    mating_move = look_for_mate_in_one(new_position)
    return mating_move is not None


