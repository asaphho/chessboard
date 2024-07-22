from typing import Dict, Union, List


class ColorPosition:

    def __init__(self, color: str, all_piece_squares: Dict[str, Union[List[str], str]],
                 short_castle: bool = True, long_castle: bool = True):
        self.color = color.lower()
        self.all_piece_squares = all_piece_squares
        self.short_castle = short_castle
        self.long_castle = long_castle

    def copy(self):
        return ColorPosition(color=self.color,
                             all_piece_squares=self.all_piece_squares.copy(),
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

    def get_king_square(self) -> str:
        if type(king_square_val := self.all_piece_squares['king']) == str:
            return king_square_val
        else:
            return king_square_val[0]

    def get_piece_type_squares(self, piece_type: str) -> List[str]:
        if piece_type.lower() not in self.all_piece_squares:
            print(f"{self.color.replace(self.color[0], self.color.upper())} has no {piece_type}.")
            raise ValueError('No such piece')
        if type(piece_square_val := self.all_piece_squares[piece_type.lower()]) == str:
            return [piece_square_val]
        else:
            return piece_square_val

    def list_unique_piece_types(self) -> List[str]:
        unique_piece_types = []
        for piece in self.all_piece_squares:
            if piece not in unique_piece_types:
                unique_piece_types.append(piece)
        return unique_piece_types

    def remove_piece_on_square(self, square: str) -> None:
        for piece in self.all_piece_squares:
            squares = self.all_piece_squares[piece]
            if type(squares) == str:
                if squares == square:
                    if piece == 'king':
                        print('Cannot remove king!')
                        raise ValueError
                    self.all_piece_squares.pop(piece)
                    return
            else:
                for i in range(len(squares)):
                    curr_square = squares[i]
                    if curr_square == square:
                        if piece == 'king':
                            print('Cannot remove king!')
                            raise ValueError
                        self.all_piece_squares[piece].pop(i)
                        if len(self.all_piece_squares[piece]) == 0:
                            self.all_piece_squares.pop(piece)
                        return
        print(f'No {self.color} piece currently on {square}!')
        raise ValueError

    def plant_piece(self, piece: str, square: str) -> None:
        if piece.lower() not in self.all_piece_squares:
            self.all_piece_squares[piece.lower()] = [square]
        else:
            curr_squares = self.all_piece_squares[piece.lower()]
            if type(curr_squares) == str:
                self.all_piece_squares[piece.lower()] = [curr_squares, square]
            else:
                self.all_piece_squares[piece.lower()].append(square)

    def promote_pawn(self, promotion_square: str, piece_promoted_to: str) -> None:
        allowed_pieces = ['queen', 'rook', 'bishop', 'knight']
        if piece_promoted_to.lower() not in allowed_pieces:
            print(f"Promotion to {piece_promoted_to.lower()} not allowed.")
            raise ValueError
        self.remove_piece_on_square(promotion_square)
        self.plant_piece(piece_promoted_to, promotion_square)

    def move_piece(self, piece: str, origin_square: str, destination_square: str) -> None:
        curr_piece_squares = self.all_piece_squares[piece.lower()]
        if type(curr_piece_squares) == str:
            self.all_piece_squares[piece.lower()] = destination_square
        else:
            for i in range(len(curr_piece_squares)):
                if curr_piece_squares[i] == origin_square:
                    self.all_piece_squares[piece.lower()].pop(i)
                    self.all_piece_squares[piece.lower()].append(destination_square)
                    break

    def get_occupied_squares(self) -> List[str]:
        occupied_squares = []
        for piece in self.all_piece_squares:
            if type(curr_piece_squares := self.all_piece_squares[piece]) == str:
                occupied_squares.append(curr_piece_squares)
            else:
                occupied_squares.extend(curr_piece_squares)
        return occupied_squares

    def get_square_piece_symbol_dict(self) -> Dict[str, str]:
        square_piece_dict = {}
        piece_symbols = {'king': 'K', 'queen': 'Q',
                         'rook': 'R', 'knight': 'N',
                         'bishop': 'B', 'pawn': 'P'}
        for piece_type in self.all_piece_squares:
            square_val = self.all_piece_squares[piece_type]
            if type(square_val) == str:
                square_piece_dict[square_val] = piece_symbols[piece_type]
            else:
                for square in square_val:
                    square_piece_dict[square] = piece_symbols[piece_type]
        return square_piece_dict


def generate_starting_position_for_color(color: str) -> ColorPosition:
    back_rank = 1 if color == 'white' else 8
    pawn_rank = 2 if color == 'white' else 7
    piece_file_dict = {'rook': ['a', 'h'], 'knight': ['b', 'g'], 'bishop': ['c', 'f'], 'queen': ['d'], 'king': ['e']}
    pieces = {}
    for piece in piece_file_dict:
        pieces[piece] = []
        for file in piece_file_dict[piece]:
            pieces[piece].append(f'{file}{back_rank}')
    pieces['pawn'] = [f'{pfile}{pawn_rank}' for pfile in 'abcdefgh']
    return ColorPosition(color=color, all_piece_squares=pieces)
