from typing import List
from classes.color_position import ColorPosition, generate_starting_position_for_color
from classes.move import LegalMove, VirtualMove
from utils.board_functions import get_intervening_squares, LETTER_TO_NUM, NUM_TO_LETTER, scan_qbr_scope, scan_kn_scope, check_squares_in_line, is_knight_move
from utils.parse_notation import piece_to_symbol

ALL_SQUARES = []
files = 'abcdefgh'
ranks = '12345678'
for f in files:
    for r in ranks:
        ALL_SQUARES.append(f'{f}{r}')


def opposite_color(color: str) -> str:
    return 'w' if color == 'b' else 'b'


def collapse_rank_string(rank_str: str) -> str:
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
        return Position(white_pieces=self.white_pieces.copy(), black_pieces=self.black_pieces.copy(),
                        side_to_move=self.to_move(), en_passant_square=self.get_en_passant_square(),
                        half_move_clock=self.get_half_move_clock(), move_number=self.get_move_number())

    def to_move(self) -> str:
        return self.side_to_move

    def is_flipped(self) -> bool:
        return self.flipped

    def flip_position(self) -> None:
        """
        Flipping position for rendering on the window
        :return:
        """
        self.flipped = not self.is_flipped()

    def change_side_to_move(self) -> None:
        self.side_to_move = opposite_color(self.to_move())

    def get_castling_rights(self) -> str:
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
        return self.white_pieces.get_occupied_squares() + self.black_pieces.get_occupied_squares() if not virtual else \
            self.virtual_white_pieces.get_occupied_squares() + self.virtual_black_pieces.get_occupied_squares()

    def reset_half_move_clock(self) -> None:
        self.half_move_clock = 0

    def set_half_move_clock(self, val: int) -> None:
        self.half_move_clock = val

    def set_move_number(self, val: int) -> None:
        self.move_number = val

    def increment_move_number(self) -> None:
        self.move_number += 1

    def increment_half_move_clock(self) -> None:
        self.half_move_clock += 1

    def get_move_number(self) -> int:
        return self.move_number

    def get_half_move_clock(self) -> int:
        return self.half_move_clock

    def set_en_passant_square(self, square: str) -> None:
        self.en_passant_square = square

    def get_en_passant_square(self) -> str:
        return self.en_passant_square

    def remove_en_passant_square(self) -> None:
        self.en_passant_square = '-'

    def get_pieces_by_color(self, color: str, virtual: bool = False) -> ColorPosition:
        if color == 'w':
            return self.white_pieces if not virtual else self.virtual_white_pieces
        else:
            return self.black_pieces if not virtual else self.virtual_black_pieces

    def scan_non_pawn_piece_moves(self, color: str, piece: str, from_square: str, virtual: bool = False) -> List[str]:
        own_piece_positions = self.get_pieces_by_color(color, virtual)
        occupied_squares = self.get_occupied_squares(virtual=virtual)
        own_pieces_squares = own_piece_positions.get_occupied_squares()
        reachable_squares = []
        if piece in ('R', 'B', 'Q'):
            scope = scan_qbr_scope(piece, from_square)
            for line_type in scope:
                for candidate_square in scope[line_type]:
                    if candidate_square in own_pieces_squares:
                        continue
                    intervening_squares = get_intervening_squares(from_square, candidate_square, line_type)
                    if len(intervening_squares) == 0:
                        reachable_squares.append(candidate_square)
                        continue
                    blocked = any([sq in occupied_squares for sq in intervening_squares])
                    if not blocked:
                        reachable_squares.append(candidate_square)
        elif piece in ('K', 'N'):
            scope = scan_kn_scope(piece, from_square)
            for candidate_square in scope:
                if candidate_square not in own_pieces_squares:
                    reachable_squares.append(candidate_square)
        else:
            raise ValueError(f'Invalid piece (\'{piece}\') for this function.')
        return reachable_squares

    def scan_pawn_non_capture_moves(self, color: str, from_square: str) -> List[str]:
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
        Use only if certain that there is an enemy piece (king excepted) on that square
        :param square:
        :return:
        """
        possible_captures = []
        to_move = self.to_move()
        own_pieces = self.get_pieces_by_color(to_move)
        occupied_squares = self.get_occupied_squares()
        for piece in own_pieces.list_unique_piece_types():
            if piece in ('Q', 'R', 'B', 'K') and square != self.get_en_passant_square():
                origin_squares = own_pieces.get_piece_type_squares(piece)
                for origin_sq in origin_squares:
                    line_type = check_squares_in_line(origin_sq, square)
                    if line_type == 'N':
                        continue
                    intervening_squares = get_intervening_squares(origin_sq, square, line_type)
                    if not intervening_squares and piece == 'K':
                        virtual_move = VirtualMove(to_move, piece, origin_sq, square)
                        is_legal = self.virtual_move_is_legal(virtual_move)
                        if is_legal:
                            possible_captures.append(self.translate_virtual_move_to_legal(virtual_move))
                    else:
                        blocked = any([int_sq in occupied_squares for int_sq in intervening_squares])
                        if blocked:
                            continue
                        if piece == 'Q':
                            virtual_move = VirtualMove(to_move, piece, origin_sq, square)
                            is_legal = self.virtual_move_is_legal(virtual_move)
                            if is_legal:
                                possible_captures.append(self.translate_virtual_move_to_legal(virtual_move))
                        elif piece == 'R' and line_type in ('r', 'f'):
                            virtual_move = VirtualMove(to_move, piece, origin_sq, square)
                            is_legal = self.virtual_move_is_legal(virtual_move)
                            if is_legal:
                                possible_captures.append(self.translate_virtual_move_to_legal(virtual_move))
                        elif piece == 'B' and line_type == 'd':
                            virtual_move = VirtualMove(to_move, piece, origin_sq, square)
                            is_legal = self.virtual_move_is_legal(virtual_move)
                            if is_legal:
                                possible_captures.append(self.translate_virtual_move_to_legal(virtual_move))
            elif piece == 'N' and square != self.get_en_passant_square():
                origin_squares = own_pieces.get_piece_type_squares('N')
                for sq in origin_squares:
                    if is_knight_move(sq, square):
                        virtual_move = VirtualMove(to_move, piece, sq, square)
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
        own_pieces = self.get_pieces_by_color(color, virtual)
        own_king_position = own_pieces.get_king_square()
        opposing_side = opposite_color(color)
        squares_attacked_by_opponent = self.scan_all_squares_attacked_by_color(opposing_side, virtual)
        return own_king_position in squares_attacked_by_opponent

    def check_for_disambiguation(self, color: str, piece: str, origin_square: str, destination_square: str) -> str:
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
        white_pieces_squares = self.white_pieces.get_square_piece_symbol_dict()
        black_pieces_squares = self.black_pieces.get_square_piece_symbol_dict()
        if square in white_pieces_squares:
            return white_pieces_squares[square]
        elif square in black_pieces_squares:
            return black_pieces_squares[square].lower()
        else:
            return '1'

    def generate_fen(self) -> str:
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
        return self.get_all_legal_moves_for_color(self.to_move())


def generate_starting_position() -> Position:
    white_pieces = generate_starting_position_for_color('w')
    black_pieces = generate_starting_position_for_color('b')
    return Position(white_pieces=white_pieces, black_pieces=black_pieces, side_to_move='w')
