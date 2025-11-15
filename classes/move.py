class LegalMove:
    """
        Represents a fully defined, legal chess move made on the board.

        This class includes information about:
        - The piece that moved and its origin/destination
        - Whether it was a capture or en passant
        - Whether it was a pawn promotion or castling move

        Attributes:
            color (str): 'w' or 'b' for the side that made the move.
            piece_moved (str): The piece type (e.g., 'P', 'N', 'K', etc.).
            origin_square (str): The square the piece moved from (e.g., 'e2').
            destination_square (str): The square the piece moved to (e.g., 'e4').
            capture (bool): True if this move captured an opponent’s piece.
            en_passant_capture (bool): True if this move was an en passant capture.
            promotion_piece (str): The piece to promote to (e.g., 'Q'), or 'None' if not applicable.
            castling (str): 'k' for kingside, 'q' for queenside, or 'N' if not a castling move.
        """

    def __init__(self, color: str, piece_type: str, origin_square: str, destination_square: str, is_capture: bool = False,
                 is_en_passant_capture: bool = False, promotion_piece: str = None, castling: str = None):
        """
            Initializes a LegalMove instance.

            Args:
                color (str): 'w' or 'b' representing the side to move.
                piece_type (str): The piece type being moved (e.g., 'P', 'N', etc.).
                origin_square (str): The square the piece is moving from.
                destination_square (str): The square the piece is moving to.
                is_capture (bool, optional): Whether this move captures an opponent's piece. Defaults to False.
                is_en_passant_capture (bool, optional): Whether this move is an en passant capture. Defaults to False.
                promotion_piece (str, optional): If a pawn promotes, this is the piece it promotes to. Defaults to None.
                castling (str, optional): 'k' for kingside, 'q' for queenside, or None if not a castling move.
            """
        self.color = color.lower()
        self.piece_moved = piece_type
        self.origin_square = origin_square
        self.destination_square = destination_square
        self.capture = is_capture
        self.en_passant_capture = is_en_passant_capture
        self.promotion_piece = promotion_piece if promotion_piece is not None else 'None'
        self.castling = castling if castling is not None else 'N'

    def get_color(self) -> str:
        """
            Returns the color of the player making this move.

            Returns:
                str: 'w' or 'b'
            """
        return self.color

    def is_king_move(self) -> bool:
        """
            Checks whether the move is made by a king.

            Returns:
                bool: True if the piece moved is a king, False otherwise.
            """
        return self.piece_moved == 'K'

    def is_pawn_move(self) -> bool:
        """
            Checks whether the move is made by a pawn.

            Returns:
                bool: True if the piece moved is a pawn, False otherwise.
            """
        return self.piece_moved == 'P'

    def is_capture(self) -> bool:
        """
            Checks whether this move captured an opponent’s piece.

            Returns:
                bool: True if this was a capture, False otherwise.
            """
        return self.capture

    def is_en_passant_capture(self) -> bool:
        """
            Checks whether this move was an en passant capture.

            Returns:
                bool: True if this move was en passant, False otherwise.
            """
        return self.en_passant_capture

    def moved_queen_rook_from_home_square(self) -> bool:
        """
            Checks whether this move involved the rook from the queenside (a-file) home square.

            Returns:
                bool: True if the queenside rook was moved from its starting square.
            """
        if self.color == 'w':
            return self.piece_moved == 'R' and self.origin_square == 'a1'
        else:
            return self.piece_moved == 'R' and self.origin_square == 'a8'

    def moved_king_rook_from_home_square(self) -> bool:
        """
            Checks whether this move involved the rook from the kingside (h-file) home square.

            Returns:
                bool: True if the kingside rook was moved from its starting square.
            """
        if self.color == 'w':
            return self.piece_moved == 'R' and self.origin_square == 'h1'
        else:
            return self.piece_moved == 'R' and self.origin_square == 'h8'

    def moved_to_opponents_queen_rook_home_square(self) -> bool:
        """
            Checks whether the move ended on the opponent's queenside rook home square.

            Returns:
                bool: True if destination was opponent's a1/a8 square.
            """
        if self.color == 'w':
            return self.destination_square == 'a8'
        else:
            return self.destination_square == 'a1'

    def moved_to_opponents_king_rook_home_square(self) -> bool:
        """
            Checks whether the move ended on the opponent's kingside rook home square.

            Returns:
                bool: True if destination was opponent's h1/h8 square.
            """
        if self.color == 'w':
            return self.destination_square == 'h8'
        else:
            return self.destination_square == 'h1'

    def is_pawn_2_square_move(self) -> bool:
        """
            Checks if this is a two-square pawn advance from the starting rank.

            Returns:
                bool: True if the pawn moved two ranks forward from its home rank.
            """
        if self.piece_moved == 'P':
            home_rank = '2' if self.color == 'w' else '7'
            two_square_destination_rank = '4' if self.color == 'w' else '5'
            return self.origin_square[1] == home_rank and self.destination_square[1] == two_square_destination_rank
        return False

    def pawn_promotion_required(self) -> bool:
        """
            Checks whether this move results in a pawn promotion.

            Returns:
                bool: True if a pawn has reached the back rank and must promote.
            """
        if self.piece_moved == 'P':
            promotion_rank = '8' if self.color == 'w' else '1'
            return self.destination_square[1] == promotion_rank
        return False

    def generate_uci(self) -> str:
        """
            Generates the UCI (Universal Chess Interface) representation of the move.

            Includes promotion suffix if applicable (e.g., 'e7e8q').

            Returns:
                str: UCI string representing the move.
            """
        uci = f'{self.origin_square}{self.destination_square}'
        if self.pawn_promotion_required():
            if self.promotion_piece == 'N':
                uci += 'n'
            else:
                uci += self.promotion_piece.lower()
        return uci


class VirtualMove:
    """
        Represents a hypothetical (unvalidated) move that could be made on the board.

        This class is used to simulate possible moves before checking legality
        (specifically, to check if the prospective move leaves the king in check or exposes it to check).

        Attributes:
            origin_square (str): The square the piece would move from.
            destination_square (str): The square the piece would move to.
            color (str): 'w' or 'b', indicating the side making the move.
            piece_type (str): The piece being moved (e.g., 'P', 'N', 'K').
        """

    def __init__(self, color: str, piece_type: str, from_square: str, to_square: str):
        """
            Initializes a VirtualMove instance.

            Args:
                color (str): The side making the move ('w' or 'b').
                piece_type (str): The type of piece making the move (e.g., 'P', 'N').
                from_square (str): The square the piece is moving from.
                to_square (str): The square the piece is moving to.
            """
        self.origin_square = from_square
        self.destination_square = to_square
        self.color = color
        self.piece_type = piece_type

    def get_origin_square(self) -> str:
        """
            Returns the origin square of the move.

            Returns:
                str: The square the piece is moving from.
            """
        return self.origin_square

    def get_destination_square(self) -> str:
        """
            Returns the destination square of the move.

            Returns:
                str: The square the piece is moving to.
            """
        return self.destination_square

    def get_color(self) -> str:
        """
            Returns the color of the player making the move.

            Returns:
                str: 'w' or 'b'.
            """
        return self.color

    def get_piece_type(self) -> str:
        """
            Returns the type of the piece being moved.

            Returns:
                str: The piece symbol (e.g., 'P', 'K', 'N').
            """
        return self.piece_type

    def results_in_promotion(self) -> bool:
        """
            Determines whether this move results in a pawn promotion.

            A promotion occurs if a pawn reaches the opposite side's back rank.

            Returns:
                bool: True if the move promotes a pawn, False otherwise.
            """
        if self.get_color() == 'w':
            if self.get_destination_square()[1] == '8' and self.get_piece_type() == 'P':
                return True
        else:
            if self.get_destination_square()[1] == '1' and self.get_piece_type() == 'P':
                return True
        return False

    def make_legal_move(self, is_capture: bool, is_en_passant_capture: bool, castling: str = None,
                        promotion_piece: str = None) -> LegalMove:
        """
            Converts this virtual move into a fully defined LegalMove. Called only after validation.

            Includes capture status, en passant, castling, and promotion information.

            Args:
                is_capture (bool): Whether the move is a capture.
                is_en_passant_capture (bool): Whether it is an en passant capture.
                castling (str, optional): 'k' for kingside, 'q' for queenside, or None if not castling.
                promotion_piece (str, optional): Piece to promote to, if applicable.

            Returns:
                LegalMove: A fully defined legal move object.
            """
        return LegalMove(color=self.get_color(),
                         piece_type=self.get_piece_type(),
                         origin_square=self.get_origin_square(),
                         destination_square=self.get_destination_square(),
                         is_capture=is_capture,
                         is_en_passant_capture=is_en_passant_capture,
                         castling=castling,
                         promotion_piece=promotion_piece)
