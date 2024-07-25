from classes.position import Position
from classes.move import LegalMove


def branch_from_position(position: Position, move: LegalMove) -> Position:
    new_position = position.copy()
    new_position.process_legal_move(move)
    return new_position


