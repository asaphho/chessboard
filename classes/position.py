from typing import List, Dict
from classes.color_position import ColorPosition, generate_starting_position_for_color
from classes.move import LegalMove, VirtualMove
from utils.board_functions import LETTER_TO_NUM, NUM_TO_LETTER, PIECE_MOVE_TYPE_DICT, SQUARE_SCOPES_MAP, INT_SQUARES_MAP
from utils.parse_notation import piece_to_symbol


def opposite_color(color: str) -> str:
    """
        Returns the opposite color in chess.

        Args:
            color (str): A single-character string representing a color ('w' or 'b').

        Returns:
            str: 'b' if input is 'w', and 'w' if input is 'b'.

        Example:
            >>> opposite_color('w')
            'b'
            >>> opposite_color('b')
            'w'
        """
    return 'w' if color == 'b' else 'b'


def collapse_rank_string(rank_str: str) -> str:
    """
        Converts a mixed string of digits and letters representing a chessboard rank
        into Forsyth-Edwards Notation (FEN) format.

        In the input string, digits represent consecutive empty squares (e.g., '3' means
        three empty squares), and letters represent pieces (e.g., 'r', 'n', 'B', etc.).
        This function compresses sequences of digits by summing them and preserves the
        order of the non-digit characters.

        For example:
            '3p3' -> '3p3'
            '111p111' -> '3p3'
            'pppppppp' -> 'pppppppp'
            '11111111' -> '8'

        Args:
            rank_str (str): The rank string to be collapsed.

        Returns:
            str: The FEN-compatible representation of the input rank.
    """
    non_numeric_range_starts = []
    numeric_range_starts = []
    if rank_str[0].isnumeric():
        numeric_range_starts.append(0)
        curr_range_numeric = True
        starts_numeric = True
    else:
        non_numeric_range_starts.append(0)
        curr_range_numeric = False
        starts_numeric = False
    for i in range(len(rank_str)):
        char = rank_str[i]
        if char.isnumeric() and not curr_range_numeric:
            numeric_range_starts.append(i)
            curr_range_numeric = True
        elif not char.isnumeric() and curr_range_numeric:
            non_numeric_range_starts.append(i)
            curr_range_numeric = False
    if not numeric_range_starts:
        return rank_str
    elif not non_numeric_range_starts:
        return '8'
    elif starts_numeric:
        fen_rank_str = ''
        if len(numeric_range_starts) > len(non_numeric_range_starts):
            non_numeric_range_starts.append(8)
        for i in range(len(numeric_range_starts)):
            numeric_range_start = numeric_range_starts[i]
            numeric_range_end = non_numeric_range_starts[i]
            fen_rank_str += str(sum([int(c) for c in rank_str[numeric_range_start:numeric_range_end]]))
            if i < len(numeric_range_starts) - 1:
                non_numeric_range_start = non_numeric_range_starts[i]
                non_numeric_range_end = numeric_range_starts[i + 1]
                fen_rank_str += rank_str[non_numeric_range_start:non_numeric_range_end]
        if non_numeric_range_starts[-1] != 8:
            fen_rank_str += rank_str[non_numeric_range_starts[-1]:]
        return fen_rank_str
    else:
        fen_rank_str = ''
        if len(non_numeric_range_starts) > len(numeric_range_starts):
            numeric_range_starts.append(8)
        for i in range(len(non_numeric_range_starts)):
            non_numeric_range_start = non_numeric_range_starts[i]
            non_numeric_range_end = numeric_range_starts[i]
            fen_rank_str += rank_str[non_numeric_range_start:non_numeric_range_end]
            if i < len(non_numeric_range_starts) - 1:
                numeric_range_start = numeric_range_starts[i]
                numeric_range_end = non_numeric_range_starts[i + 1]
                fen_rank_str += str(sum([int(c) for c in rank_str[numeric_range_start:numeric_range_end]]))
        if numeric_range_starts[-1] != 8:
            fen_rank_str += str(sum([int(c) for c in rank_str[numeric_range_starts[-1]:]]))
        return fen_rank_str


class Position:
    """
        Represents the full state of a chess game, including piece positions, turn information,
        move counters, en passant status, and board orientation.

        This class manages both the real and virtual positions of white and black pieces.
        Virtual copies are used for move simulation and legality checking, such as verifying
        whether a move leaves the king in check.

        Attributes:
            white_pieces (ColorPosition): The actual positions of all white pieces.
            black_pieces (ColorPosition): The actual positions of all black pieces.
            virtual_white_pieces (ColorPosition): A deep copy of white_pieces, used to evaluate move legality.
            virtual_black_pieces (ColorPosition): A deep copy of black_pieces, used to evaluate move legality.
            side_to_move (str): The side to move next, either 'w' or 'b' (stored in lowercase).
            en_passant_square (str): The en passant target square (e.g., 'e6'), or '-' if none.
            half_move_clock (int): Number of half-moves since the last capture or pawn move (for the 50-move rule).
            move_number (int): The full move number, incremented after Black’s move.
            flipped (bool): Whether the board should be rendered from Black’s perspective (True) or White’s (False).

        Args:
            white_pieces (ColorPosition): Current positions of White's pieces.
            black_pieces (ColorPosition): Current positions of Black's pieces.
            side_to_move (str): Which side is to move next ('w' or 'b').
            en_passant_square (str, optional): Square available for en passant, or '-' if not applicable. Defaults to '-'.
            half_move_clock (int, optional): Half-move clock for the 50-move draw rule. Defaults to 0.
            move_number (int, optional): Full move number, starting from 1. Defaults to 1.
            flipped (bool, optional): If True, board rendering is flipped (Black's perspective). Defaults to False.

        Example:
            >>> white_pieces = ColorPosition(color='w', all_piece_squares={'K': ['e1'], 'R': ['c4']})
            >>> black_pieces = ColorPosition(color='b', all_piece_squares={'K': ['e5'], 'B': ['e6']})
            >>> pos = Position(white_pieces, black_pieces, 'w')
            >>> pos.virtual_white_pieces.get_king_square()
            'e1'
        """

    def __init__(self, white_pieces: ColorPosition, black_pieces: ColorPosition, side_to_move: str,
                 en_passant_square: str = '-',
                 half_move_clock: int = 0, move_number: int = 1, flipped: bool = False):
        self.white_pieces = white_pieces
        self.virtual_white_pieces = white_pieces.copy()
        self.black_pieces = black_pieces
        self.virtual_black_pieces = black_pieces.copy()
        self.en_passant_square = en_passant_square
        self.half_move_clock = half_move_clock
        self.move_number = move_number
        self.side_to_move = side_to_move.lower()
        self.flipped = flipped  # for rendering on the gui

    def copy(self):
        """
            Creates a deep copy of the current Position object.

            Returns:
                Position: A new Position instance with copied piece positions, turn information,
                en passant status, move counters, and flipped state.
            """
        return Position(white_pieces=self.white_pieces.copy(), black_pieces=self.black_pieces.copy(),
                        side_to_move=self.to_move(), en_passant_square=self.get_en_passant_square(),
                        half_move_clock=self.get_half_move_clock(), move_number=self.get_move_number())

    def to_move(self) -> str:
        """
            Returns the color of the side whose turn it is to move.

            Returns:
                str: 'w' if it's White's turn, 'b' if it's Black's.
            """
        return self.side_to_move

    def is_flipped(self) -> bool:
        """
            Indicates whether the board is flipped for rendering (i.e., from Black's perspective).

            Returns:
                bool: True if flipped, False otherwise.
            """
        return self.flipped

    def flip_position(self) -> None:
        """
    Toggles the board's orientation for rendering purposes.

    If the board is currently shown from White's perspective, it will switch
    to Black's, and vice versa. Does not affect game logic or piece positions.
    """
        self.flipped = not self.is_flipped()

    def change_side_to_move(self) -> None:
        """
            Switches the side to move to the opposite color.

            Used for progressing the turn after a move is made.
            """
        self.side_to_move = opposite_color(self.to_move())

    def get_castling_rights(self) -> str:
        """
            Returns a FEN-style string representing the current castling rights for both sides.

            Uppercase letters represent White's rights:
                - 'K' for kingside (short) castling
                - 'Q' for queenside (long) castling

            Lowercase letters represent Black's rights:
                - 'k' for kingside (short) castling
                - 'q' for queenside (long) castling

            If no castling is available for either side, returns '-'.

            Returns:
                str: A string like 'KQkq', 'Kq', or '-' depending on castling availability.
            """
        castling_rights = ''
        if self.white_pieces.can_short_castle():
            castling_rights += 'K'
        if self.white_pieces.can_long_castle():
            castling_rights += 'Q'
        if self.black_pieces.can_short_castle():
            castling_rights += 'k'
        if self.black_pieces.can_long_castle():
            castling_rights += 'q'
        if castling_rights == '':
            return '-'
        else:
            return castling_rights

    def get_occupied_squares(self, virtual: bool = False) -> List[str]:
        """
            Returns a list of all squares currently occupied by pieces, optionally using virtual positions.

            Args:
                virtual (bool, optional): If True, uses the virtual piece positions (e.g., for move validation).
                                          If False, uses the actual piece positions. Defaults to False.

            Returns:
                List[str]: A list of square strings (e.g., ['e1', 'd2']) occupied by either side.
            """
        return self.white_pieces.get_occupied_squares() + self.black_pieces.get_occupied_squares() if not virtual else \
            self.virtual_white_pieces.get_occupied_squares() + self.virtual_black_pieces.get_occupied_squares()

    def reset_half_move_clock(self) -> None:
        """
           Resets the half-move clock to 0.

           This is called after a pawn move or a capture,
           as required by the fifty-move rule.
           """
        self.half_move_clock = 0

    def set_half_move_clock(self, val: int) -> None:
        """
            Sets the half-move clock to a specific value.

            Args:
                val (int): The number of half-moves since the last pawn move or capture.
            """
        self.half_move_clock = val

    def set_move_number(self, val: int) -> None:
        """
            Sets the full move number.

            Args:
                val (int): The full move number (starts at 1 and increments after Black's move).
            """
        self.move_number = val

    def increment_move_number(self) -> None:
        """
            Increments the full move number by 1.

            Called after Black completes a move.
            """
        self.move_number += 1

    def increment_half_move_clock(self) -> None:
        """
            Increments the half-move clock by 1.

            Used when a move is made that is not a pawn move or a capture.
            """
        self.half_move_clock += 1

    def get_move_number(self) -> int:
        """
            Returns the current full move number.

            Returns:
                int: The full move number (e.g., 1, 2, 3, ...).
            """
        return self.move_number

    def get_half_move_clock(self) -> int:
        """
            Returns the current half-move clock value.

            Returns:
                int: The number of half-moves since the last pawn move or capture.
            """
        return self.half_move_clock

    def set_en_passant_square(self, square: str) -> None:
        """
            Sets the en passant target square.

            Args:
                square (str): The square available for en passant (e.g., 'e6').
            """
        self.en_passant_square = square

    def get_en_passant_square(self) -> str:
        """
            Returns the en passant target square.

            Returns:
                str: The square available for en passant, or '-' if none.
            """
        return self.en_passant_square

    def remove_en_passant_square(self) -> None:
        """
            Clears the en passant target square by setting it to '-'.
        """
        self.en_passant_square = '-'

    def get_pieces_by_color(self, color: str, virtual: bool = False) -> ColorPosition:
        """
            Retrieves the ColorPosition object for the specified color.

            Args:
                color (str): 'w' or 'b', for white or black.
                virtual (bool, optional): If True, returns the virtual (simulated) position.
                                          If False, returns the actual position. Defaults to False.

            Returns:
                ColorPosition: The position object for the specified color.
            """
        if color == 'w':
            return self.white_pieces if not virtual else self.virtual_white_pieces
        else:
            return self.black_pieces if not virtual else self.virtual_black_pieces

    def scan_non_pawn_piece_moves(self, color: str, piece: str, from_square: str, virtual: bool = False) -> List[str]:
        """
            Returns all destination squares for a non-pawn piece from a given square,
            considering blocking by own or intervening pieces.

            Args:
                color (str): 'w' or 'b', the piece's color.
                piece (str): Piece type (e.g., 'Q', 'R', 'B', 'N', 'K').
                from_square (str): The square the piece is on.
                virtual (bool, optional): Whether to use virtual board state. Defaults to False.

            Returns:
                List[str]: Squares the piece can move to (ignoring check).
            """
        own_piece_positions = self.get_pieces_by_color(color, virtual)
        occupied_squares = self.get_occupied_squares(virtual=virtual)
        own_pieces_squares = own_piece_positions.get_occupied_squares()
        reachable_squares = []
        scopes = SQUARE_SCOPES_MAP[from_square]
        allowed_move_types = PIECE_MOVE_TYPE_DICT[piece]
        for move_type in allowed_move_types:
            candidate_squares = scopes[move_type]
            for dest_sq in candidate_squares:
                if dest_sq in own_pieces_squares:
                    continue
                if f'{from_square}{dest_sq}' in INT_SQUARES_MAP:
                    intervening_squares = INT_SQUARES_MAP[f'{from_square}{dest_sq}']['int']
                    blocked = any([int_sq in occupied_squares for int_sq in intervening_squares])
                    if not blocked:
                        reachable_squares.append(dest_sq)
                else:
                    reachable_squares.append(dest_sq)
        return reachable_squares

    def scan_pawn_non_capture_moves(self, color: str, from_square: str) -> List[str]:
        """
            Returns all non-capturing forward moves for a pawn from a given square (without checking whether king is exposed to or left in check by that move).

            Takes into account starting position and blocked squares.

            Args:
                color (str): 'w' or 'b', the pawn's color.
                from_square (str): The current square of the pawn.

            Returns:
                List[str]: Squares the pawn can advance to without capturing, without checking whether king is exposed to or left in check by that move.
            """
        occupied_squares = self.get_occupied_squares()
        file = from_square[0]
        rank = int(from_square[1])
        home_rank = 2 if color == 'w' else 7
        rank_delta = 1 if color == 'w' else -1
        if rank == home_rank:
            if f'{file}{home_rank + rank_delta}' in occupied_squares:
                return []
            elif f'{file}{home_rank + (2 * rank_delta)}' in occupied_squares:
                return [f'{file}{home_rank + rank_delta}']
            else:
                return [f'{file}{home_rank + rank_delta}', f'{file}{home_rank + (2 * rank_delta)}']
        else:
            return [f'{file}{rank + rank_delta}'] if f'{file}{rank + rank_delta}' not in occupied_squares else []

    def scan_pawn_attacked_squares(self, color: str, from_square: str) -> List[str]:
        """
            Returns the diagonal squares that a pawn attacks from a given square.

            Args:
                color (str): 'w' or 'b', the pawn's color.
                from_square (str): The square the pawn occupies.

            Returns:
                List[str]: Squares that the pawn threatens diagonally forward.
            """
        file = from_square[0]
        file_num = LETTER_TO_NUM[file]
        rank = int(from_square[1])
        if 1 < file_num < 8:
            neighboring_files = [NUM_TO_LETTER[f] for f in (file_num - 1, file_num + 1)]
        elif file_num == 1:
            neighboring_files = ['b']
        else:
            neighboring_files = ['g']
        delta_rank = 1 if color == 'w' else -1
        target_rank = rank + delta_rank
        return [f"{f}{target_rank}" for f in neighboring_files]

    def scan_all_squares_attacked_by_color(self, color: str, virtual: bool = False) -> List[str]:
        """
            Returns all squares currently attacked by pieces of the specified color.

            Includes both pawn and non-pawn threats, using actual or virtual board state.

            Args:
                color (str): 'w' or 'b'.
                virtual (bool, optional): If True, use virtual position state. Defaults to False.

            Returns:
                List[str]: List of all squares currently threatened by the given side.
            """
        attacked_squares = []
        piece_positions = self.get_pieces_by_color(color, virtual)
        for piece_type in piece_positions.list_unique_piece_types():
            squares_occupied_by_that_piece_type = piece_positions.get_piece_type_squares(piece_type)
            if piece_type != 'P':
                for square in squares_occupied_by_that_piece_type:
                    attacked_squares.extend(self.scan_non_pawn_piece_moves(color, piece_type, square, virtual))
            else:
                for square in squares_occupied_by_that_piece_type:
                    attacked_squares.extend(self.scan_pawn_attacked_squares(color, square))
        return attacked_squares

    def scan_all_captures_to_square(self, square: str) -> List[LegalMove]:
        """
        Returns a list of all legal moves that would result in capturing a piece
        on the given square by the side to move.

        This assumes an enemy piece (other than a king) is present on the square.

        Args:
            square (str): The square where a piece is targeted for capture.

        Returns:
            List[LegalMove]: All legal capturing moves to that square.
        """
        possible_captures = []
        to_move = self.to_move()
        own_pieces = self.get_pieces_by_color(to_move)
        occupied_squares = self.get_occupied_squares()
        for piece in own_pieces.list_unique_piece_types():
            if piece != 'P' and square != self.get_en_passant_square():
                allowed_move_types = PIECE_MOVE_TYPE_DICT[piece]
                origin_squares = own_pieces.get_piece_type_squares(piece)
                for origin_sq in origin_squares:
                    scopes = SQUARE_SCOPES_MAP[origin_sq]
                    for move_type in allowed_move_types:
                        destination_squares = scopes[move_type]
                        if square not in destination_squares:
                            continue
                        if f'{origin_sq}{square}' in INT_SQUARES_MAP:
                            intervening_squares = INT_SQUARES_MAP[f'{origin_sq}{square}']['int']
                            blocked = any([int_sq in occupied_squares for int_sq in intervening_squares])
                            if not blocked:
                                virtual_move = VirtualMove(to_move, piece, origin_sq, square)
                                is_legal = self.virtual_move_is_legal(virtual_move)
                                if is_legal:
                                    possible_captures.append(self.translate_virtual_move_to_legal(virtual_move))
                        else:
                            virtual_move = VirtualMove(to_move, piece, origin_sq, square)
                            is_legal = self.virtual_move_is_legal(virtual_move)
                            if is_legal:
                                possible_captures.append(self.translate_virtual_move_to_legal(virtual_move))
            elif piece == 'P':
                pawn_squares = own_pieces.get_piece_type_squares('P')
                for pawn_sq in pawn_squares:
                    attacked_squares = self.scan_pawn_attacked_squares(to_move, pawn_sq)
                    if square in attacked_squares:
                        virtual_move = VirtualMove(to_move, piece, pawn_sq, square)
                        is_legal = self.virtual_move_is_legal(virtual_move)
                        promotion = virtual_move.results_in_promotion()
                        if is_legal and promotion:
                            for pp in ('Q', 'R', 'N', 'B'):
                                possible_captures.append(self.translate_virtual_move_to_legal(virtual_move, pp))
                        elif is_legal and not promotion:
                            possible_captures.append(self.translate_virtual_move_to_legal(virtual_move))
        return possible_captures

    def is_under_check(self, color: str, virtual: bool = False) -> bool:
        """
            Determines whether the king of the specified color is currently in check.

            Evaluates whether any opposing piece is attacking the square occupied by the king.
            Can use either the actual or virtual board state.

            Args:
                color (str): 'w' or 'b', the color of the king being evaluated.
                virtual (bool, optional): If True, evaluates check on the virtual board state.
                                          Defaults to False.

            Returns:
                bool: True if the king is in check, False otherwise.
            """
        own_pieces = self.get_pieces_by_color(color, virtual)
        own_king_position = own_pieces.get_king_square()
        opposing_side = opposite_color(color)
        squares_attacked_by_opponent = self.scan_all_squares_attacked_by_color(opposing_side, virtual)
        return own_king_position in squares_attacked_by_opponent

    def check_for_disambiguation(self, color: str, piece: str, origin_square: str, destination_square: str) -> str:
        """
            Determines how to disambiguate a move in algebraic notation when multiple identical
            pieces of the same type can move to the same destination square.

            Args:
                color (str): 'w' or 'b', the moving side.
                piece (str): The piece type (e.g., 'N', 'R', etc.).
                origin_square (str): The square the piece is moving from.
                destination_square (str): The square the piece is moving to.

            Returns:
                str:
                    - 'N' if no disambiguation is needed.
                    - 'f' to disambiguate by file.
                    - 'r' to disambiguate by rank.
                    - 's' to disambiguate by full square (file + rank).
            """
        piece_positions = self.get_pieces_by_color(color)
        squares_occupied_by_piece = piece_positions.get_piece_type_squares(piece)
        if len(squares_occupied_by_piece) == 1:
            return 'N'
        origin_squares_that_can_reach_destination = []
        for occupied_square in squares_occupied_by_piece:
            reachable_squares = self.scan_non_pawn_piece_moves(color, piece, occupied_square)
            if destination_square in reachable_squares:
                origin_squares_that_can_reach_destination.append(occupied_square)
        if len(origin_squares_that_can_reach_destination) == 1:
            return 'N'
        origin_file = origin_square[0]
        disambiguate_by_file = [square for square in origin_squares_that_can_reach_destination if
                                square[0] == origin_file]
        if len(disambiguate_by_file) == 1:
            return 'f'
        origin_rank = origin_square[1]
        disambiguate_by_rank = [square for square in origin_squares_that_can_reach_destination if
                                square[1] == origin_rank]
        if len(disambiguate_by_rank) == 1:
            return 'r'
        return 's'

    def process_legal_move(self, move: LegalMove) -> str:
        """
            Executes a legal move on the board, updates game state, and returns the algebraic notation of the move.

            This method handles:
            - Castling rights updates
            - En passant square management
            - Piece captures (including en passant)
            - Pawn promotion
            - Move counters and turn changes
            - Piece movement and board state updates
            - Generating move notation (including disambiguation and check/mate markers)

            Args:
                move (LegalMove): The move to process. Assumed to be already validated as legal.

            Returns:
                str: The move written in standard algebraic notation (e.g., "e4", "Nf3", "O-O", "Qxe5+").
            """
        color_moved = move.get_color()
        opposing_color = opposite_color(color_moved)
        notation_move_number = self.get_move_number()
        if move.piece_moved not in ('K', 'P'):
            disambiguation = self.check_for_disambiguation(color_moved, move.piece_moved,
                                                           move.origin_square, move.destination_square)
        else:
            disambiguation = 'N'
        if color_moved == 'b':
            self.increment_move_number()
        if move.is_king_move():
            self.get_pieces_by_color(color_moved).disable_castling()
        if move.moved_king_rook_from_home_square():
            self.get_pieces_by_color(color_moved).disable_short_castling()
        if move.moved_queen_rook_from_home_square():
            self.get_pieces_by_color(color_moved).disable_long_castling()
        if move.moved_to_opponents_king_rook_home_square():
            self.get_pieces_by_color(opposing_color).disable_short_castling()
        if move.moved_to_opponents_queen_rook_home_square():
            self.get_pieces_by_color(opposing_color).disable_long_castling()
        if move.is_pawn_move() or move.is_capture():
            self.reset_half_move_clock()
        else:
            self.increment_half_move_clock()
        if move.is_pawn_2_square_move():
            file = move.destination_square[0]
            if color_moved == 'w':
                self.set_en_passant_square(f"{file}3")
            else:
                self.set_en_passant_square(f"{file}6")
        else:
            self.remove_en_passant_square()
        if move.is_capture():
            if not move.is_en_passant_capture():
                self.get_pieces_by_color(opposing_color).remove_piece_on_square(move.destination_square)
            else:
                file = move.destination_square[0]
                rank_to_remove = 5 if color_moved == 'w' else 4
                self.get_pieces_by_color(opposite_color(color_moved)).remove_piece_on_square(f'{file}{rank_to_remove}')
        back_rank = '1' if color_moved == 'w' else '8'
        if move.castling == 'k':
            self.get_pieces_by_color(color_moved).move_piece('R', f'h{back_rank}', f'f{back_rank}')
        elif move.castling == 'q':
            self.get_pieces_by_color(color_moved).move_piece('R', f'a{back_rank}', f'd{back_rank}')

        # ACTUAL PIECE MOVEMENT HERE
        self.get_pieces_by_color(color_moved).move_piece(move.piece_moved, move.origin_square, move.destination_square)

        if move.pawn_promotion_required():
            self.get_pieces_by_color(color_moved).promote_pawn(move.destination_square, move.promotion_piece)
        self.virtual_white_pieces = self.white_pieces.copy()
        self.virtual_black_pieces = self.black_pieces.copy()

        # PRODUCE NOTATION
        notation_move_str = f'{notation_move_number}. ' if color_moved == 'w' else f'{notation_move_number}... '
        if move.is_king_move():
            if move.castling == 'k':
                notation_move_str += 'O-O'
            elif move.castling == 'q':
                notation_move_str += 'O-O-O'
            else:
                notation_move_str += 'K'
                if move.is_capture():
                    notation_move_str += 'x'
                notation_move_str += move.destination_square
        elif move.is_pawn_move():
            if move.is_capture():
                notation_move_str += f'{move.origin_square[0]}x{move.destination_square}'
            else:
                notation_move_str += f'{move.destination_square}'
            if move.pawn_promotion_required():
                notation_move_str += '=' + piece_to_symbol(move.promotion_piece)
        else:
            notation_move_str += piece_to_symbol(move.piece_moved)
            if disambiguation != 'N':
                if disambiguation == 'f':
                    notation_move_str += move.origin_square[0]
                elif disambiguation == 'r':
                    notation_move_str += move.origin_square[1]
                else:
                    notation_move_str += move.origin_square
            if move.is_capture():
                notation_move_str += 'x'
            notation_move_str += move.destination_square
        self.change_side_to_move()
        if self.is_under_check(self.to_move()):
            legal_moves_available = self.get_all_legal_moves_for_color(self.to_move())
            if len(legal_moves_available) == 0:
                notation_move_str += '#'
            else:
                notation_move_str += '+'
        return notation_move_str

    def look_at_square(self, square: str) -> str:
        """
            Returns the symbol representing the piece on the given square.

            - Uppercase for white pieces
            - Lowercase for black pieces
            - '1' if the square is unoccupied

            Args:
                square (str): The square to inspect (e.g., 'e4').

            Returns:
                str: Piece symbol (e.g., 'K', 'p', 'N') or '1' if empty.
            """
        white_pieces_squares = self.white_pieces.get_square_piece_symbol_dict()
        black_pieces_squares = self.black_pieces.get_square_piece_symbol_dict()
        if square in white_pieces_squares:
            return white_pieces_squares[square]
        elif square in black_pieces_squares:
            return black_pieces_squares[square].lower()
        else:
            return '1'

    def generate_fen(self) -> str:
        """
            Generates the FEN (Forsyth-Edwards Notation) string representing the current position.

            Includes:
            - Piece placement
            - Side to move
            - Castling rights
            - En passant target square
            - Half-move clock
            - Full move number

            Returns:
                str: The full FEN string describing the current board state.

            Example:
                >>> pos = generate_starting_position()
                >>> pos.generate_fen()
                'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
            """
        ranks = '87654321'
        files = 'abcdefgh'
        fen_rank_strs = []
        for rank in ranks:
            rank_str = ''
            for file in files:
                square = file + rank
                rank_str += self.look_at_square(square)
            rank_str = collapse_rank_string(rank_str)
            fen_rank_strs.append(rank_str)
        fen_str = '/'.join(fen_rank_strs)
        fen_str += f' {self.to_move()[0].lower()}'
        fen_str += f' {self.get_castling_rights()}'
        fen_str += f' {self.get_en_passant_square()}'
        fen_str += f' {self.get_half_move_clock()}'
        fen_str += f' {self.get_move_number()}'
        return fen_str

    def castling_legal_here(self, color: str, side: str) -> bool:
        """
            Determines whether castling is legal for a given color and side (kingside or queenside).

            Checks:
            - The king and rook are on their original squares
            - The player has not lost castling rights
            - The king is not in check
            - Squares between the king and rook are unoccupied
            - The king does not pass through or land on an attacked square

            Args:
                color (str): 'w' or 'b' indicating the side attempting to castle.
                side (str): 'k' for kingside, 'q' for queenside.

            Returns:
                bool: True if castling is legal, False otherwise.
            """
        back_rank = '1' if color == 'w' else '8'
        own_piece_positions = self.get_pieces_by_color(color)
        opposing_color = opposite_color(color)
        if own_piece_positions.get_king_square() != f'e{back_rank}':
            return False
        rook_home_file = 'a' if side == 'q' else 'h'
        square_piece_symbol_dict = own_piece_positions.get_square_piece_symbol_dict()
        if f'{rook_home_file}{back_rank}' not in square_piece_symbol_dict:
            return False
        elif square_piece_symbol_dict[f'{rook_home_file}{back_rank}'] != 'R':
            return False

        if self.is_under_check(color):
            return False

        if not own_piece_positions.can_castle_on_side(side):
            return False

        squares_to_be_empty = [f'{file}{back_rank}' for file in ('f', 'g')] if side == 'k' \
            else [f'{file}{back_rank}' for file in ('b', 'c', 'd')]
        squares_that_must_not_be_attacked = [f'f{back_rank}', f'g{back_rank}'] if side == 'k' \
            else [f'c{back_rank}', f'd{back_rank}']

        squares_attacked_by_opponent = self.scan_all_squares_attacked_by_color(opposing_color)
        occupied_squares = self.get_occupied_squares()

        if any([square in occupied_squares for square in squares_to_be_empty]):
            return False
        if any([square in squares_attacked_by_opponent for square in squares_that_must_not_be_attacked]):
            return False
        return True

    def virtual_move_is_legal(self, virtual_move: VirtualMove) -> bool:
        """
            Checks if a virtual move is legal by simulating it and testing for king safety.

            Simulates the move on the virtual board, handles special rules like castling
            and en passant, and determines whether the moving side's king would be in check.

            Args:
                virtual_move (VirtualMove): The move to evaluate.

            Returns:
                bool: True if the move is legal (does not leave king in check), False otherwise.
            """
        side_attempting_move = virtual_move.get_color()
        piece_typed_moved = virtual_move.get_piece_type()
        origin_square = virtual_move.get_origin_square()
        destination_square = virtual_move.get_destination_square()
        if piece_typed_moved == 'K':
            if side_attempting_move == 'w' and origin_square == 'e1' and destination_square == 'g1':
                return self.castling_legal_here(side_attempting_move, 'k')
            elif side_attempting_move == 'w' and origin_square == 'e1' and destination_square == 'c1':
                return self.castling_legal_here(side_attempting_move, 'q')
            elif side_attempting_move == 'b' and origin_square == 'e8' and destination_square == 'g8':
                return self.castling_legal_here(side_attempting_move, 'k')
            elif side_attempting_move == 'b' and origin_square == 'e8' and destination_square == 'c8':
                return self.castling_legal_here(side_attempting_move, 'q')
        opposing_side = opposite_color(side_attempting_move)
        opposing_piece_squares = self.get_pieces_by_color(opposing_side, virtual=True)
        own_piece_squares = self.get_pieces_by_color(side_attempting_move, virtual=True)
        if destination_square in opposing_piece_squares.get_occupied_squares():
            opposing_piece_squares.remove_piece_on_square(destination_square)

        own_piece_squares.move_piece(piece_typed_moved, virtual_move.get_origin_square(),
                                     destination_square)
        if destination_square == self.get_en_passant_square() and piece_typed_moved == 'P':
            file = destination_square[0]
            if side_attempting_move == 'w':
                opposing_piece_squares.remove_piece_on_square(f'{file}5')
            else:
                opposing_piece_squares.remove_piece_on_square(f"{file}4")
        results_in_check = self.is_under_check(side_attempting_move, virtual=True)
        self.virtual_white_pieces = self.white_pieces.copy()
        self.virtual_black_pieces = self.black_pieces.copy()
        return not results_in_check

    def translate_virtual_move_to_legal(self, virtual_move: VirtualMove, promotion_piece: str = None) -> LegalMove:
        """
            Converts a validated virtual move into a fully specified legal move.

            Adds legality details such as whether the move is a capture, a promotion,
            en passant, or castling.

            Args:
                virtual_move (VirtualMove): The virtual move to translate.
                promotion_piece (str, optional): Piece to promote to (e.g., 'Q'). Required only for promotions.

            Returns:
                LegalMove: A fully defined LegalMove object, including move metadata.
            """
        side_attempting_move = virtual_move.get_color()
        piece_typed_moved = virtual_move.get_piece_type()
        origin_square = virtual_move.get_origin_square()
        destination_square = virtual_move.get_destination_square()
        opposing_side_pieces = self.get_pieces_by_color(opposite_color(side_attempting_move))
        is_capture = destination_square in opposing_side_pieces.get_occupied_squares()
        if destination_square == self.get_en_passant_square() and piece_typed_moved == 'P':
            is_capture = True
            is_en_passant_capture = True
        else:
            is_en_passant_capture = False
        if piece_typed_moved == 'K':
            if side_attempting_move == 'w' and origin_square == 'e1' and destination_square == 'g1':
                castling = 'k'
            elif side_attempting_move == 'w' and origin_square == 'e1' and destination_square == 'c1':
                castling = 'q'
            elif side_attempting_move == 'b' and origin_square == 'e8' and destination_square == 'g8':
                castling = 'k'
            elif side_attempting_move == 'b' and origin_square == 'e8' and destination_square == 'c8':
                castling = 'q'
            else:
                castling = None
        else:
            castling = None
        return virtual_move.make_legal_move(is_capture=is_capture,
                                            is_en_passant_capture=is_en_passant_capture,
                                            castling=castling,
                                            promotion_piece=promotion_piece)

    def scrape_virtual_moves_for_color(self, color: str) -> List[VirtualMove]:
        """
            Generates all possible virtual moves for a given color, regardless of legality.

            This includes:
            - All standard moves for non-pawn pieces
            - All pawn advances and captures
            - En passant opportunities
            - Castling options (kingside and queenside)

            The legality of these moves is not guaranteed — use `virtual_move_is_legal`
            to filter them.

            Args:
                color (str): 'w' or 'b'

            Returns:
                List[VirtualMove]: All candidate virtual moves for the given side.
            """
        piece_position = self.get_pieces_by_color(color)
        opposing_piece_position = self.get_pieces_by_color(opposite_color(color))
        piece_types = piece_position.list_unique_piece_types()
        virtual_moves = []
        for piece in piece_types:
            squares_occupied_by_that_piece_type = piece_position.get_piece_type_squares(piece)
            for origin_square in squares_occupied_by_that_piece_type:
                if piece != 'P':
                    reachable_squares = self.scan_non_pawn_piece_moves(color, piece, origin_square)
                    for reachable_square in reachable_squares:
                        virtual_moves.append(VirtualMove(color, piece, origin_square, reachable_square))
                    if piece == 'K' and color == 'w' and origin_square == 'e1':
                        virtual_moves.extend([VirtualMove(color, piece, 'e1', 'g1'),
                                              VirtualMove(color, piece, 'e1', 'c1')])
                    elif piece == 'K' and color == 'b' and origin_square == 'e8':
                        virtual_moves.extend([VirtualMove(color, piece, 'e8', 'g8'),
                                              VirtualMove(color, piece, 'e8', 'c8')])
                else:
                    reachable_squares = self.scan_pawn_non_capture_moves(color, origin_square)
                    for reachable_square in reachable_squares:
                        virtual_moves.append(VirtualMove(color, piece, origin_square, reachable_square))
                    attacked_squares = self.scan_pawn_attacked_squares(color, origin_square)
                    for attacked_square in attacked_squares:
                        if attacked_square in opposing_piece_position.get_occupied_squares():
                            virtual_moves.append(VirtualMove(color, piece, origin_square, attacked_square))
                        elif attacked_square == self.get_en_passant_square():
                            en_passant_target_rank = '6' if color == 'w' else '3'
                            if attacked_square[1] == en_passant_target_rank:
                                virtual_moves.append(VirtualMove(color, piece, origin_square, attacked_square))
        return virtual_moves

    def get_all_legal_moves_for_color(self, color: str) -> List[LegalMove]:
        """
            Generates all legal moves for the specified color.

            This filters the list of all virtual moves for legality (e.g., king safety),
            and handles promotion options by expanding each valid promotion into
            multiple legal moves with promotion types.

            Args:
                color (str): 'w' or 'b'.

            Returns:
                List[LegalMove]: List of all fully-defined legal moves for the given side.
            """
        virtual_moves = self.scrape_virtual_moves_for_color(color)
        legal_moves = []
        for virtual_move in virtual_moves:
            move_is_legal = self.virtual_move_is_legal(virtual_move)
            if move_is_legal:
                if virtual_move.results_in_promotion():
                    for promotion_piece in ['Q', 'R', 'N', 'B']:
                        legal_moves.append(self.translate_virtual_move_to_legal(virtual_move, promotion_piece))
                else:
                    legal_moves.append(self.translate_virtual_move_to_legal(virtual_move))
        return legal_moves

    def get_all_legal_moves_for_side_to_move(self) -> List[LegalMove]:
        """
            Returns all legal moves available for the side whose turn it is to move.

            Shortcut to `get_all_legal_moves_for_color(self.to_move())`.

            Returns:
                List[LegalMove]: Legal moves for the side to move.
            """
        return self.get_all_legal_moves_for_color(self.to_move())

    def get_piece_scope_dict(self, color: str) -> Dict[str, List[str]]:
        """
            Returns a dictionary mapping each piece (by type and origin square) to the squares it can threaten.

            This includes:
            - All pseudo-legal moves for non-pawn pieces, filtered for blockages.
            - Diagonal attack scopes for pawns.

            Useful for visualizing piece influence or potential threats.

            Args:
                color (str): 'w' or 'b'.

            Returns:
                Dict[str, List[str]]: Keys are piece IDs like 'Nd2' or 'Pe4', values are lists of destination squares.
            """
        piece_scope_dict = {}
        piece_positions = self.get_pieces_by_color(color)
        occupied_squares = self.get_occupied_squares()
        for piece in piece_positions.list_unique_piece_types():
            origin_squares = piece_positions.get_piece_type_squares(piece)
            if piece != 'P':
                allowed_move_types = PIECE_MOVE_TYPE_DICT[piece]
                for origin_sq in origin_squares:
                    dict_key = f'{piece}{origin_sq}'
                    piece_scope_dict[dict_key] = []
                    scopes = SQUARE_SCOPES_MAP[origin_sq]
                    for move_type in allowed_move_types:
                        destination_squares = scopes[move_type]
                        for dest_sq in destination_squares:
                            if f'{origin_sq}{dest_sq}' in INT_SQUARES_MAP:
                                intervening_squares = INT_SQUARES_MAP[f'{origin_sq}{dest_sq}']['int']
                                blocked = any([int_sq in occupied_squares for int_sq in intervening_squares])
                                if not blocked:
                                    piece_scope_dict[dict_key].append(dest_sq)
                            else:
                                piece_scope_dict[dict_key].append(dest_sq)
            else:
                for pawn_sq in origin_squares:
                    dict_key = f'P{pawn_sq}'
                    piece_scope_dict[dict_key] = self.scan_pawn_attacked_squares(color, pawn_sq)
        return piece_scope_dict


def generate_starting_position() -> Position:
    """
        Creates and returns a Position object representing the standard chess starting position.

        Initializes:
        - White and black pieces in their initial configurations
        - White to move
        - Default castling rights, move counters, and no en passant square

        Returns:
            Position: The initial game state for a standard chess match.

        Example:
            >>> pos = generate_starting_position()
            >>> pos.generate_fen()
            'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
        """
    white_pieces = generate_starting_position_for_color('w')
    black_pieces = generate_starting_position_for_color('b')
    return Position(white_pieces=white_pieces, black_pieces=black_pieces, side_to_move='w')
