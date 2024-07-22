from typing import List
from classes.color_position import ColorPosition
from classes.move import LegalMove, VirtualMove
from utils.board_functions import (check_squares_in_line, get_intervening_squares, is_knight_move, LETTER_TO_NUM,
                                   NUM_TO_LETTER)

ALL_SQUARES = []
files = 'abcdefgh'
ranks = '12345678'
for f in files:
    for r in ranks:
        ALL_SQUARES.append(f'{f}{r}')


def opposite_color(color: str) -> str:
    return 'white' if color.lower().startswith('b') else 'black'


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
                 half_move_clock: int = 0, move_number: int = 1):
        self.white_pieces = white_pieces
        self.virtual_white_pieces = white_pieces.copy()
        self.black_pieces = black_pieces
        self.virtual_black_pieces = black_pieces.copy()
        self.en_passant_square = en_passant_square
        self.half_move_clock = half_move_clock
        self.move_number = move_number
        self.all_squares = []
        self.side_to_move = side_to_move.lower()

    def to_move(self) -> str:
        return self.side_to_move

    def change_side_to_move(self) -> None:
        if self.to_move().lower().startswith('w'):
            self.side_to_move = 'black'
        elif self.to_move().lower().startswith('b'):
            self.side_to_move = 'white'

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

    def scan_non_pawn_piece_moves(self, color: str, piece: str, from_square: str, virtual: bool = False) -> List[str]:
        if color.lower() == 'white':
            own_piece_positions = self.white_pieces if not virtual else self.virtual_white_pieces
        else:
            own_piece_positions = self.black_pieces if not virtual else self.virtual_black_pieces
        occupied_squares = self.get_occupied_squares(virtual=virtual)
        own_pieces_squares = own_piece_positions.get_occupied_squares()
        all_other_squares = [square for square in ALL_SQUARES
                             if square != from_square and square not in own_pieces_squares]
        reachable_squares = []
        for candidate_square in all_other_squares:
            check_line = check_squares_in_line(from_square, candidate_square)
            knight_move = is_knight_move(from_square, candidate_square)
            if check_line != 'Not in line':
                intervening_squares = get_intervening_squares(from_square, candidate_square, check_line)
                if len(intervening_squares) == 0:
                    if piece == 'queen' or piece == 'king':
                        reachable_squares.append(candidate_square)
                else:
                    blocked = any([square in occupied_squares for square in intervening_squares])
                    if not blocked:
                        if piece == 'queen':
                            reachable_squares.append(candidate_square)
                        elif piece == 'rook' and (check_line == 'file' or check_line == 'rank'):
                            reachable_squares.append(candidate_square)
                        elif piece == 'bishop' and check_line == 'diagonal':
                            reachable_squares.append(candidate_square)
            elif knight_move and piece == 'knight':
                reachable_squares.append(candidate_square)
        return reachable_squares

    def scan_pawn_non_capture_moves(self, color: str, from_square: str) -> List[str]:
        occupied_squares = self.get_occupied_squares()
        file = from_square[0]
        rank = int(from_square[1])
        if color.lower() == 'white':
            if rank == 2:
                if f"{file}3" in occupied_squares:
                    return []
                elif f"{file}4" in occupied_squares:
                    return [f"{file}3"]
                else:
                    return [f"{file}3", f"{file}4"]
            else:
                return [f"{file}{rank + 1}"] if f"{file}{rank + 1}" not in occupied_squares else []
        else:
            if rank == 7:
                if f"{file}6" in occupied_squares:
                    return []
                elif f"{file}5" in occupied_squares:
                    return [f"{file}6"]
                else:
                    return [f"{file}6", f"{file}5"]
            else:
                return [f"{file}{rank - 1}"] if f"{file}{rank - 1}" not in occupied_squares else []

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
        delta_rank = 1 if color.lower() == 'white' else -1
        target_rank = rank + delta_rank
        return [f"{f}{target_rank}" for f in neighboring_files]

    def scan_all_squares_attacked_by_color(self, color: str, virtual: bool = False) -> List[str]:
        attacked_squares = []
        if color.lower() == 'white':
            piece_positions = self.white_pieces if not virtual else self.virtual_white_pieces
        else:
            piece_positions = self.black_pieces if not virtual else self.virtual_black_pieces
        for piece_type in piece_positions.list_unique_piece_types():
            squares_occupied_by_that_piece_type = piece_positions.get_piece_type_squares(piece_type)
            if piece_type != 'pawn':
                for square in squares_occupied_by_that_piece_type:
                    attacked_squares.extend(self.scan_non_pawn_piece_moves(color, piece_type, square, virtual))
            else:
                for square in squares_occupied_by_that_piece_type:
                    attacked_squares.extend(self.scan_pawn_attacked_squares(color, square))
        return attacked_squares

    def is_under_check(self, color: str, virtual: bool = False) -> bool:
        if color.lower() == 'white':
            own_king_position = self.white_pieces.get_king_square() if not virtual else self.virtual_white_pieces
            return own_king_position in self.scan_all_squares_attacked_by_color('black', virtual)
        else:
            own_king_position = self.black_pieces.get_king_square() if not virtual else self.virtual_black_pieces
            return own_king_position in self.scan_all_squares_attacked_by_color('white', virtual)

    def process_legal_move(self, move: LegalMove):
        color_moved = move.get_color()
        if color_moved == 'black':
            self.increment_move_number()
        if move.is_king_move():
            if color_moved == 'white':
                self.white_pieces.disable_castling()
            else:
                self.black_pieces.disable_castling()
        if move.moved_king_rook_from_home_square():
            if color_moved == 'white':
                self.white_pieces.disable_short_castling()
            else:
                self.black_pieces.disable_short_castling()
        if move.moved_queen_rook_from_home_square():
            if color_moved == 'white':
                self.white_pieces.disable_long_castling()
            else:
                self.black_pieces.disable_long_castling()
        if move.moved_to_opponents_king_rook_home_square():
            if color_moved == 'white':
                self.black_pieces.disable_short_castling()
            else:
                self.white_pieces.disable_short_castling()
        if move.moved_to_opponents_queen_rook_home_square():
            if color_moved == 'white':
                self.black_pieces.disable_long_castling()
            else:
                self.white_pieces.disable_long_castling()
        if move.is_pawn_move() or move.is_capture():
            self.reset_half_move_clock()
        else:
            self.increment_half_move_clock()
        if move.is_pawn_2_square_move():
            file = move.destination_square[0]
            if color_moved == 'white':
                self.set_en_passant_square(f"{file}3")
            else:
                self.set_en_passant_square(f"{file}6")
        else:
            self.remove_en_passant_square()
        if move.is_capture():
            if not move.is_en_passant_capture():
                if color_moved == 'white':
                    self.black_pieces.remove_piece_on_square(move.destination_square)
                else:
                    self.white_pieces.remove_piece_on_square(move.destination_square)
            else:
                file = move.destination_square[0]
                if color_moved == 'white':
                    self.black_pieces.remove_piece_on_square(f"{file}5")
                else:
                    self.white_pieces.remove_piece_on_square(f"{file}4")
        if str(move.castling).lower().startswith('k') or str(move.castling).lower().startswith('short'):
            if color_moved == 'white':
                self.white_pieces.move_piece('rook', 'h1', 'f1')
            else:
                self.black_pieces.move_piece('rook', 'h8', 'f8')
        elif str(move.castling).lower().startswith('q') or str(move.castling).lower().startswith('long'):
            if color_moved == 'white':
                self.white_pieces.move_piece('rook', 'a1', 'd1')
            else:
                self.black_pieces.move_piece('rook', 'a8', 'd8')
        if color_moved == 'white':
            self.white_pieces.move_piece(move.piece_moved, move.origin_square, move.destination_square)
        else:
            self.black_pieces.move_piece(move.piece_moved, move.origin_square, move.destination_square)
        if move.pawn_promotion_required():
            if color_moved == 'white':
                self.white_pieces.promote_pawn(move.destination_square, move.promotion_piece)
            else:
                self.black_pieces.promote_pawn(move.destination_square, move.promotion_piece)
        self.virtual_white_pieces = self.white_pieces.copy()
        self.virtual_black_pieces = self.black_pieces.copy()
        self.change_side_to_move()

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
        if self.is_under_check(color):
            return False
        if color == 'white':
            if side.lower().startswith('k') or side.lower().startswith('short'):
                if not self.white_pieces.can_short_castle():
                    return False
                if any([square in self.get_occupied_squares() for square in ['f1', 'g1']]):
                    return False
                if any([square in self.scan_all_squares_attacked_by_color('black') for square in ['f1', 'g1']]):
                    return False
                return True
            else:
                if not self.white_pieces.can_long_castle():
                    return False
                if any([square in self.get_occupied_squares() for square in ['d1', 'c1', 'b1']]):
                    return False
                if any([square in self.scan_all_squares_attacked_by_color('black')] for square in ['d1', 'c1']):
                    return False
                return True
        else:
            if side.lower().startswith('k') or side.lower().startswith('short'):
                if not self.black_pieces.can_short_castle():
                    return False
                if any([square in self.get_occupied_squares() for square in ['f8', 'g8']]):
                    return False
                if any([square in self.scan_all_squares_attacked_by_color('white') for square in ['f8', 'g8']]):
                    return False
                return True
            else:
                if not self.black_pieces.can_long_castle():
                    return False
                if any([square in self.get_occupied_squares() for square in ['d8', 'c8', 'b8']]):
                    return False
                if any([square in self.scan_all_squares_attacked_by_color('white') for square in ['d8', 'c8']]):
                    return False
                return True

    def virtual_move_is_legal(self, virtual_move: VirtualMove) -> bool:
        side_attempting_move = 'white' if virtual_move.get_color().lower().startswith('w') else 'black'
        piece_typed_moved = virtual_move.get_piece_type()
        origin_square = virtual_move.get_origin_square()
        destination_square = virtual_move.get_destination_square()
        if piece_typed_moved == 'king':
            if side_attempting_move == 'white' and origin_square == 'e1' and destination_square == 'g1':
                return self.castling_legal_here(side_attempting_move, 'kingside')
            elif side_attempting_move == 'white' and origin_square == 'e1' and destination_square == 'c1':
                return self.castling_legal_here(side_attempting_move, 'queenside')
            elif side_attempting_move == 'black' and origin_square == 'e8' and destination_square == 'g8':
                return self.castling_legal_here(side_attempting_move, 'kingside')
            elif side_attempting_move == 'black' and origin_square == 'e8' and destination_square == 'c8':
                return self.castling_legal_here(side_attempting_move, 'queenside')
        opposing_side = opposite_color(side_attempting_move)
        opposing_piece_squares = self.virtual_black_pieces if opposing_side == 'black' else self.virtual_white_pieces
        own_piece_squares = self.virtual_white_pieces if side_attempting_move == 'white' else self.virtual_black_pieces
        if destination_square in opposing_piece_squares.get_occupied_squares():
            opposing_piece_squares.remove_piece_on_square(destination_square)

        own_piece_squares.move_piece(piece_typed_moved, virtual_move.get_origin_square(),
                                     destination_square)
        if destination_square == self.get_en_passant_square() and piece_typed_moved == 'pawn':
            file = destination_square[0]
            if side_attempting_move == 'white':
                opposing_piece_squares.remove_piece_on_square(f'{file}5')
            else:
                opposing_piece_squares.remove_piece_on_square(f"{file}4")
        results_in_check = self.is_under_check(side_attempting_move, virtual=True)
        self.virtual_white_pieces = self.white_pieces.copy()
        self.virtual_black_pieces = self.black_pieces.copy()
        return not results_in_check

    def translate_virtual_move_to_legal(self, virtual_move: VirtualMove, promotion_piece: str = None) -> LegalMove:
        side_attempting_move = 'white' if virtual_move.get_color().lower().startswith('w') else 'black'
        piece_typed_moved = virtual_move.get_piece_type()
        origin_square = virtual_move.get_origin_square()
        destination_square = virtual_move.get_destination_square()
        opposing_side_pieces = self.black_pieces if side_attempting_move == 'white' else self.white_pieces
        is_capture = destination_square in opposing_side_pieces.get_occupied_squares()
        if destination_square == self.get_en_passant_square() and piece_typed_moved == 'pawn':
            is_capture = True
            is_en_passant_capture = True
        else:
            is_en_passant_capture = False
        if piece_typed_moved == 'king':
            if side_attempting_move == 'white' and origin_square == 'e1' and destination_square == 'g1':
                castling = 'kingside'
            elif side_attempting_move == 'white' and origin_square == 'e1' and destination_square == 'c1':
                castling = 'queenside'
            elif side_attempting_move == 'black' and origin_square == 'e8' and destination_square == 'g8':
                castling = 'kingside'
            elif side_attempting_move == 'black' and origin_square == 'e8' and destination_square == 'c8':
                castling = 'queenside'
            else:
                castling = None
        else:
            castling = None
        return virtual_move.make_legal_move(is_capture=is_capture,
                                            is_en_passant_capture=is_en_passant_capture,
                                            castling=castling,
                                            promotion_piece=promotion_piece)

    def scrape_virtual_moves_for_color(self, color: str) -> List[VirtualMove]:
        piece_position = self.white_pieces if color == 'white' else self.black_pieces
        opposing_piece_position = self.black_pieces if color == 'white' else self.white_pieces
        piece_types = piece_position.list_unique_piece_types()
        virtual_moves = []
        for piece in piece_types:
            squares_occupied_by_that_piece_type = piece_position.get_piece_type_squares(piece)
            for origin_square in squares_occupied_by_that_piece_type:
                if piece != 'pawn':
                    reachable_squares = self.scan_non_pawn_piece_moves(color, piece, origin_square)
                    for reachable_square in reachable_squares:
                        virtual_moves.append(VirtualMove(color, piece, origin_square, reachable_square))
                    if piece == 'king' and color == 'white' and origin_square == 'e1':
                        virtual_moves.extend([VirtualMove(color, piece, 'e1', 'g1'),
                                              VirtualMove(color, piece, 'e1', 'c1')])
                    elif piece == 'king' and color == 'black' and origin_square == 'e8':
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
                            virtual_moves.append(VirtualMove(color, piece, origin_square, attacked_square))
        return virtual_moves


