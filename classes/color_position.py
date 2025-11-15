from typing import Dict, List
from copy import deepcopy


class ColorPosition:
    """
    Represents the board position of all pieces for a single color in a chess game.

    Attributes:
        color (str): The color of the pieces ('w' or 'b', case-insensitive).
        all_piece_squares (Dict[str, List[str]]): A dictionary mapping piece types
            ('K', 'Q', 'R', 'B', 'N', 'P') to lists of squares they occupy.
        short_castle (bool): Whether short (kingside) castling is still possible.
        long_castle (bool): Whether long (queenside) castling is still possible.

    Args:
        color (str): A single-character string indicating the color ('w' or 'b').
        all_piece_squares (Dict[str, List[str]]): Dictionary of piece positions, where keys
            are uppercase piece symbols ('K', 'Q', 'R', 'B', 'N', 'P') and values are
            lists of square strings (e.g., 'e3', 'h5').
        short_castle (bool, optional): Whether short castling is possible. Defaults to True.
        long_castle (bool, optional): Whether long castling is possible. Defaults to True.

    Examples:
        >>> position = ColorPosition(
        ...     color='w',
        ...     all_piece_squares={
        ...         'K': ['e1'],
        ...         'Q': ['d1'],
        ...         'R': ['a1', 'h1'],
        ...         'B': ['c1', 'f1'],
        ...         'N': ['b1', 'g1'],
        ...         'P': ['a2', 'b2', 'c2', 'd2', 'e2', 'f2', 'g2', 'h2']
        ...     },
        ...     short_castle=True,
        ...     long_castle=True
        ... )

        >>> position.color
        'w'

        >>> position.all_piece_squares['K']
        ['e1']

        >>> position.short_castle
        True
    """

    def __init__(self, color: str, all_piece_squares: Dict[str, List[str]],
                 short_castle: bool = True, long_castle: bool = True):
        self.color = color.lower()
        self.all_piece_squares = deepcopy(all_piece_squares)
        self.short_castle = short_castle
        self.long_castle = long_castle

    def copy(self):
        """
            Creates a deep copy of the current ColorPosition instance.

            Returns:
                ColorPosition: A new instance with the same color, piece positions,
                and castling rights. Modifying the copy will not affect the original.

            Example:
                >>> original = ColorPosition('w', {'K': ['e1'], 'P': ['a2', 'b2']})
                >>> clone = original.copy()
                >>> clone.all_piece_squares['P'].append('c2')
                >>> 'c2' in original.all_piece_squares['P']
                False
            """
        return ColorPosition(color=self.color,
                             all_piece_squares=self.all_piece_squares,
                             short_castle=self.short_castle,
                             long_castle=self.long_castle)

    def disable_short_castling(self) -> None:
        """
            Disables the ability to castle on the kingside (short castling) for this color.
        """
        self.short_castle = False

    def disable_long_castling(self) -> None:
        """
            Disables the ability to castle on the queenside (long castling) for this color.
        """
        self.long_castle = False

    def disable_castling(self) -> None:
        """
            Disables both short (kingside) and long (queenside) castling for this color.
        """
        self.disable_short_castling()
        self.disable_long_castling()

    def can_short_castle(self) -> bool:
        """
            Checks whether short (kingside) castling is currently allowed.

            Returns:
                bool: True if short castling is allowed, False otherwise.
        """
        return self.short_castle

    def can_long_castle(self) -> bool:
        """
            Checks whether long (queenside) castling is currently allowed.

            Returns:
                bool: True if long castling is allowed, False otherwise.
        """
        return self.long_castle

    def can_castle_on_side(self, side: str) -> bool:
        """
            Checks whether castling is allowed on the specified side.

            Args:
                side (str): Either 'k' for kingside or any other value for queenside.

            Returns:
                bool: True if castling is allowed on the given side, False otherwise.
        """
        if side == 'k':
            return self.can_short_castle()
        else:
            return self.can_long_castle()

    def get_king_square(self) -> str:
        """
            Returns the square occupied by the king of this color.

            Assumes there is exactly one king, and it is the first entry in the list
            for the 'K' key in all_piece_squares.

            Returns:
                str: The square the king is on (e.g., 'e1').
        """
        return self.all_piece_squares['K'][0]

    def get_piece_type_squares(self, piece_type: str) -> List[str]:
        """
            Returns a list of squares occupied by pieces of the given type.

            Args:
                piece_type (str): A single uppercase letter representing the piece type
                    ('P', 'B', 'N', 'R', 'Q', or 'K').

            Returns:
                List[str]: List of square strings where the specified piece type is located.
                           Returns an empty list if the piece type is not present.
        """
        if piece_type not in self.all_piece_squares:
            return []
        else:
            squares = self.all_piece_squares[piece_type]
            return squares

    def list_unique_piece_types(self) -> List[str]:
        """
            Lists all unique piece types currently present for this color.

            Returns:
                List[str]: A list of uppercase piece symbols ('P', 'N', 'B', 'R', 'Q', 'K')
                           that are currently on the board.
        """
        unique_piece_types = []
        for piece in self.all_piece_squares:
            if piece not in unique_piece_types:
                unique_piece_types.append(piece)
        return unique_piece_types

    def remove_piece_on_square(self, square: str) -> None:
        """
            Removes the piece occupying the specified square.

            Searches through all piece types and removes the one that occupies the given square.
            If no piece is found on the square, raises a ValueError.

            Args:
                square (str): The board square to remove a piece from (e.g., 'e4').

            Raises:
                ValueError: If no piece is found on the specified square.
            """
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
            Places a piece on the given square.

            Adds the square to the list of squares for the given piece type.

            Args:
                piece (str): The uppercase symbol of the piece ('P', 'B', 'N', 'R', 'Q', or 'K').
                square (str): The square to place the piece on (e.g., 'd5').
            """
        if piece not in self.all_piece_squares:
            self.all_piece_squares[piece] = [square]
        else:
            self.all_piece_squares[piece].append(square)

    def promote_pawn(self, promotion_square: str, piece_promoted_to: str) -> None:
        """
        Promotes a pawn on the specified square to another piece.

        Removes the pawn from the promotion square and replaces it with the promoted piece.
        Only allows promotion to 'Q', 'R', 'B', or 'N'.

        Args:
            promotion_square (str): The square where the pawn is being promoted.
            piece_promoted_to (str): The piece to promote to ('Q', 'R', 'B', or 'N').

        Raises:
            ValueError: If an invalid piece is specified for promotion.
        """
        allowed_pieces = ['Q', 'R', 'B', 'N']
        if piece_promoted_to not in allowed_pieces:
            print(f"Promotion to {piece_promoted_to} not allowed.")
            raise ValueError
        self.remove_piece_on_square(promotion_square)
        self.plant_piece(piece_promoted_to, promotion_square)

    def move_piece(self, piece: str, origin_square: str, destination_square: str) -> None:
        """
            Moves a piece from one square to another.

            Finds the specified piece on the origin square and updates its position
            to the destination square.

            Args:
                piece (str): The uppercase symbol of the piece to move ('P', 'B', etc.).
                origin_square (str): The current square of the piece.
                destination_square (str): The square to move the piece to.
            """
        curr_piece_squares = self.all_piece_squares[piece]
        for i in range(len(curr_piece_squares)):
            if curr_piece_squares[i] == origin_square:
                self.all_piece_squares[piece].pop(i)
                self.all_piece_squares[piece].append(destination_square)
                break

    def get_occupied_squares(self) -> List[str]:
        """
            Returns a list of all squares currently occupied by this color's pieces.

            Returns:
                List[str]: List of square strings (e.g., ['e4', 'd5']) where this color's
                pieces are located.
            """
        occupied_squares = []
        for piece in self.all_piece_squares:
            occupied_squares.extend(self.all_piece_squares[piece])
        return occupied_squares

    def get_square_piece_symbol_dict(self, lowercase: bool = False) -> Dict[str, str]:
        """
           Returns a mapping from each occupied square to the symbol of the piece on that square.

           Args:
               lowercase (bool, optional): If True, returns piece symbols in lowercase.
                   Defaults to False (uppercase symbols).

           Returns:
               Dict[str, str]: A dictionary mapping squares (e.g., 'e4') to piece symbols
               (e.g., 'P' or 'p').

           Example:
               >>> position = ColorPosition(color='w', all_piece_squares={'K': ['e1'], 'Q': ['d1']})
               >>> position.get_square_piece_symbol_dict()
               {'e1': 'K', 'd1': 'Q'}

               >>> position.get_square_piece_symbol_dict(lowercase=True)
               {'e1': 'k', 'd1': 'q'}
           """
        square_piece_dict = {}
        for piece_type in self.all_piece_squares:
            squares = self.all_piece_squares[piece_type]
            for square in squares:
                square_piece_dict[square] = piece_type if not lowercase else piece_type.lower()
        return square_piece_dict


def generate_starting_position_for_color(color: str) -> ColorPosition:
    """
        Generates the standard starting position for a given color in chess.

        This function returns a `ColorPosition` object representing the initial
        piece placements for either white or black, with pawns on the second rank
        and major/minor pieces on the first rank, in standard configuration.

        Args:
            color (str): The color for which to generate the starting position.
                Must be 'w' (white) or 'b' (black). Case-sensitive.

        Returns:
            ColorPosition: A `ColorPosition` instance representing the starting
            piece layout for the given color, with default castling rights.

        Example:
            >>> white_start = generate_starting_position_for_color('w')
            >>> white_start.get_piece_type_squares('P')
            ['a2', 'b2', 'c2', 'd2', 'e2', 'f2', 'g2', 'h2']

            >>> black_start = generate_starting_position_for_color('b')
            >>> black_start.get_piece_type_squares('K')
            ['e8']
        """
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
