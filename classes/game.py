from classes.position import generate_starting_position
from classes.move import LegalMove
from utils.parse_notation import check_for_castling, find_piece_moved_and_destination_square,\
    check_for_disambiguating_string, piece_to_symbol


class Game:

    def __init__(self):
        self.current_position = generate_starting_position()
        self.fen_record_dict = {self.current_position.generate_fen().rsplit(' ', maxsplit=2)[0]: 1}
        self.moves_record = {}

    def process_move(self, legal_move: LegalMove) -> str:
        move_notation = self.current_position.process_legal_move(legal_move)
        current_fen = self.current_position.generate_fen()
        current_fen_for_record = current_fen.rsplit(' ', maxsplit=2)[0]
        if current_fen_for_record in self.fen_record_dict:
            self.fen_record_dict[current_fen_for_record] += 1
        else:
            self.fen_record_dict[current_fen_for_record] = 1
        if self.current_position.to_move() == 'white':
            notation_move_number = self.current_position.get_move_number() - 1
        else:
            notation_move_number = self.current_position.get_move_number()
        if notation_move_number in self.moves_record:
            self.moves_record[notation_move_number].append(move_notation)
        else:
            self.moves_record[notation_move_number] = [move_notation]
        return move_notation

    def drawn_by_repetition(self) -> bool:
        return any([self.fen_record_dict[fen] >= 3 for fen in self.fen_record_dict])

    def drawn_by_50_move_rule(self) -> bool:
        return self.current_position.get_half_move_clock() >= 100

    def drawn_by_reduction(self) -> bool:
        white_pieces = self.current_position.white_pieces
        black_pieces = self.current_position.black_pieces
        unique_white_pieces = white_pieces.list_unique_piece_types()
        unique_black_pieces = black_pieces.list_unique_piece_types()
        if any([piece in ('queen', 'rook', 'pawn') for piece in unique_white_pieces + unique_black_pieces]):
            return False
        if any([len(piece_list) >= 3 for piece_list in [unique_white_pieces, unique_black_pieces]]):
            return False
        if unique_black_pieces == ['king'] and unique_white_pieces == ['king']:
            return True
        if 'bishop' in unique_white_pieces and 'knight' not in unique_white_pieces:
            white_insufficient_material = len(white_pieces.get_piece_type_squares('bishop')) == 1
            white_has_minor_piece = True
        elif 'knight' in unique_white_pieces and 'bishop' not in unique_white_pieces:
            white_insufficient_material = len(white_pieces.get_piece_type_squares('knight')) == 1
            white_has_minor_piece = True
        else:
            white_insufficient_material = True
            white_has_minor_piece = False
        if not white_insufficient_material:
            return False
        if 'bishop' in unique_black_pieces and 'knight' not in unique_black_pieces:
            black_insufficient_material = len(black_pieces.get_piece_type_squares('bishop')) == 1
            black_has_minor_piece = True
        elif 'knight' in unique_black_pieces and 'bishop' not in unique_black_pieces:
            black_insufficient_material = len(black_pieces.get_piece_type_squares('knight')) == 1
            black_has_minor_piece = True
        else:
            black_insufficient_material = True
            black_has_minor_piece = False
        if not black_insufficient_material:
            return False
        if white_has_minor_piece:
            return not black_has_minor_piece
        else:
            return True

    def check_game_end_conditions(self) -> str:
        if self.drawn_by_repetition():
            return 'Drawn by repetition.'
        if self.drawn_by_50_move_rule():
            return 'Drawn by 50-move rule.'
        if self.drawn_by_reduction():
            return 'Drawn by reduction.'
        side_to_move = self.current_position.to_move()
        legal_moves_available = self.current_position.get_all_legal_moves_for_color(side_to_move)
        if len(legal_moves_available) == 0:
            if self.current_position.is_under_check(side_to_move):
                if side_to_move == 'white':
                    return 'Black wins by checkmate.'
                else:
                    return 'White wins by checkmate.'
            else:
                return 'Drawn by stalemate.'
        else:
            return 'None'

    def process_input_notation(self, notation_str: str) -> str:
        castling = check_for_castling(notation_str)
        if castling == 'None':
            piece_moved, destination_square = find_piece_moved_and_destination_square(notation_str)
        elif castling == 'kingside':
            piece_moved = 'king'
            if self.current_position.to_move() == 'white':
                destination_square = 'g1'
            else:
                destination_square = 'g8'
        else:
            piece_moved = 'king'
            if self.current_position.to_move() == 'white':
                destination_square = 'c1'
            else:
                destination_square = 'c8'
        if piece_moved not in ('king', 'pawn'):
            disambiguating_string = check_for_disambiguating_string(notation_str, destination_square,
                                                                    piece_to_symbol(piece_moved))
        else:
            disambiguating_string = 'None'




