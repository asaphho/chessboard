from typing import Dict, List
from copy import deepcopy


class ColorPosition:

    def __init__(self, color: str, all_piece_squares: Dict[str, List[str]],
                 short_castle: bool = True, long_castle: bool = True):
        self.color = color.lower()
        self.all_piece_squares = deepcopy(all_piece_squares)
        self.short_castle = short_castle
        self.long_castle = long_castle

    def copy(self):
        return ColorPosition(color=self.color,
                             all_piece_squares=self.all_piece_squares,
                             short_castle=self.short_castle,
                             long_castle=self.long_castle)

    def disable_short_castling(self) -> None:
        self.short_castle = False

    def disable_long_castling(self) -> None:
        self.long_castle = False

    def disable_castling(self) -> None:
        self.disable_short_castling()
        self.disable_long_castling()

    def can_short_castle(self) -> bool:
        return self.short_castle

    def can_long_castle(self) -> bool:
        return self.long_castle

    def can_castle_on_side(self, side: str) -> bool:
        if side == 'k':
            return self.can_short_castle()
        else:
            return self.can_long_castle()

    def get_king_square(self) -> str:
        return self.all_piece_squares['K'][0]

    def get_piece_type_squares(self, piece_type: str) -> List[str]:
        """

        :param piece_type: 'P', 'B', 'N' ,'R', 'Q', or 'K'
        :return:
        """
        if piece_type not in self.all_piece_squares:
            return []
        else:
            squares = self.all_piece_squares[piece_type]
            return squares

    def list_unique_piece_types(self) -> List[str]:
        unique_piece_types = []
        for piece in self.all_piece_squares:
            if piece not in unique_piece_types:
                unique_piece_types.append(piece)
        return unique_piece_types

    def remove_piece_on_square(self, square: str) -> None:
        for piece in self.all_piece_squares:
            squares = self.all_piece_squares[piece]
            for i in range(len(squares)):
                curr_square = squares[i]
                if curr_square == square:
                    self.all_piece_squares[piece].pop(i)
                    if len(self.all_piece_squares[piece]) == 0:
                        self.all_piece_squares.pop(piece)
                    return
        print(f'No {self.color} piece currently on {square}!')
        raise ValueError

    def plant_piece(self, piece: str, square: str) -> None:
        """

        :param piece: 'P', 'B', 'N', 'R', 'Q', 'K'
        :param square:
        :return:
        """
        if piece not in self.all_piece_squares:
            self.all_piece_squares[piece] = [square]
        else:
            self.all_piece_squares[piece].append(square)

    def promote_pawn(self, promotion_square: str, piece_promoted_to: str) -> None:
        """

        :param promotion_square:
        :param piece_promoted_to: 'Q', 'R', 'B', 'N'
        :return:
        """
        allowed_pieces = ['Q', 'R', 'B', 'N']
        if piece_promoted_to not in allowed_pieces:
            print(f"Promotion to {piece_promoted_to} not allowed.")
            raise ValueError
        self.remove_piece_on_square(promotion_square)
        self.plant_piece(piece_promoted_to, promotion_square)

    def move_piece(self, piece: str, origin_square: str, destination_square: str) -> None:
        curr_piece_squares = self.all_piece_squares[piece]
        for i in range(len(curr_piece_squares)):
            if curr_piece_squares[i] == origin_square:
                self.all_piece_squares[piece].pop(i)
                self.all_piece_squares[piece].append(destination_square)
                break

    def get_occupied_squares(self) -> List[str]:
        occupied_squares = []
        for piece in self.all_piece_squares:
            occupied_squares.extend(self.all_piece_squares[piece])
        return occupied_squares

    def get_square_piece_symbol_dict(self) -> Dict[str, str]:
        square_piece_dict = {}
        for piece_type in self.all_piece_squares:
            squares = self.all_piece_squares[piece_type]
            for square in squares:
                square_piece_dict[square] = piece_type
        return square_piece_dict


def generate_starting_position_for_color(color: str) -> ColorPosition:
    back_rank = 1 if color == 'w' else 8
    pawn_rank = 2 if color == 'w' else 7
    piece_file_dict = {'R': ['a', 'h'], 'N': ['b', 'g'], 'B': ['c', 'f'], 'Q': ['d'], 'K': ['e']}
    pieces = {}
    for piece in piece_file_dict:
        pieces[piece] = []
        for file in piece_file_dict[piece]:
            pieces[piece].append(f'{file}{back_rank}')
    pieces['P'] = [f'{pfile}{pawn_rank}' for pfile in 'abcdefgh']
    return ColorPosition(color=color, all_piece_squares=pieces)
