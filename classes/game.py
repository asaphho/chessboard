from classes.position import generate_starting_position
from classes.move import LegalMove
from utils.parse_notation import check_for_castling, find_piece_moved_and_destination_square,\
    check_for_disambiguating_string, piece_to_symbol, check_for_promotion_piece, pawn_capture_origin_file
import sys
from copy import deepcopy


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
        side_to_move = self.current_position.to_move()
        castling = check_for_castling(notation_str)
        if castling == 'None':
            piece_moved, destination_square = find_piece_moved_and_destination_square(notation_str)
            all_legal_moves = self.current_position.get_all_legal_moves_for_color(side_to_move)
            possible_legal_moves = [move for move in all_legal_moves if move.piece_moved == piece_moved]
            if len(possible_legal_moves) == 0:
                print(f'Illegal move.')
                raise ValueError
            possible_legal_moves = [move for move in possible_legal_moves if move.destination_square == destination_square]
            if len(possible_legal_moves) == 0:
                print(f'Illegal move.')
                raise ValueError
            if piece_moved == 'king':
                if check_for_disambiguating_string(notation_str, destination_square, 'K') != 'None':
                    print('Disambiguation ignored for king move.')
                return self.process_move(possible_legal_moves[0])
            elif piece_moved != 'pawn':
                disambiguating_string = check_for_disambiguating_string(notation_str, destination_square,
                                                                        piece_to_symbol(piece_moved))
                if disambiguating_string == 'None' and len(possible_legal_moves) > 1:
                    print(f'Ambiguity detected. More than one {piece_moved} can move to {destination_square}.')
                    raise ValueError
                elif disambiguating_string == 'None' and len(possible_legal_moves) == 1:
                    return self.process_move(possible_legal_moves[0])
                elif len(disambiguating_string) == 1 and disambiguating_string.isalpha():
                    possible_legal_moves = [move for move in possible_legal_moves if move.origin_square[0] == disambiguating_string]
                    if len(possible_legal_moves) > 1:
                        print(f'Ambiguity detected. More than one {piece_moved} can reach {destination_square} from the {disambiguating_string}-file.')
                        raise ValueError
                    elif len(possible_legal_moves) == 0:
                        print(f'No {piece_moved} on {disambiguating_string}-file able to move to {destination_square}.')
                        raise ValueError
                    else:
                        return self.process_move(possible_legal_moves[0])
                elif len(disambiguating_string) == 1 and disambiguating_string.isnumeric():
                    possible_legal_moves = [move for move in possible_legal_moves if move.origin_square[1] == disambiguating_string]
                    if len(possible_legal_moves) > 1:
                        print(f'Ambiguity detected. More than one {piece_moved} on rank {disambiguating_string} can reach {destination_square}.')
                        raise ValueError
                    elif len(possible_legal_moves) == 0:
                        print(f'No {piece_moved} able to move to {destination_square} from rank {disambiguating_string}.')
                    else:
                        return self.process_move(possible_legal_moves[0])
                elif len(disambiguating_string) == 2:
                    possible_legal_moves = [move for move in possible_legal_moves if move.origin_square == disambiguating_string]
                    if len(possible_legal_moves) == 0:
                        print(f'No {piece_moved} on {disambiguating_string} to move to {destination_square}.')
                        raise ValueError
                    else:
                        return self.process_move(possible_legal_moves[0])
                else:
                    print(f'Something went wrong: Unhandled disambiguation string {disambiguating_string}.')
                    h = input()
                    sys.exit(1)
            else:
                promotion_rank = '1' if side_to_move == 'black' else '8'
                if destination_square[1] == promotion_rank:
                    promotion_piece = check_for_promotion_piece(notation_str, destination_square)
                    if promotion_piece == 'None':
                        print(f'Promotion piece required as pawn has reached last rank. Add Q, R, B, or N right after the destination square.')
                        raise ValueError
                    capture_origin_file = pawn_capture_origin_file(notation_str, destination_square)
                    if capture_origin_file == 'None':
                        for move in possible_legal_moves:
                            if move.promotion_piece == promotion_piece and not move.is_capture():
                                return self.process_move(move)
                        print('Something went wrong. Pawn reached last rank but no pawn promotion LegalMove objects found to match promotion piece.')
                        h = input()
                        sys.exit(1)
                    else:
                        for move in possible_legal_moves:
                            if move.origin_square[0] == capture_origin_file and move.promotion_piece == promotion_piece and move.is_capture():
                                return self.process_move(move)
                        print('Something went wrong. Pawn reached last rank but no pawn promotion LegalMove objects found to match promotion piece.')
                        h = input()
                        sys.exit(1)
                else:
                    capture_origin_file = pawn_capture_origin_file(notation_str, destination_square)
                    if capture_origin_file == 'None':
                        for move in possible_legal_moves:
                            if not move.is_capture():
                                return self.process_move(move)
                        # code can reach here in the case of a pawn attempting to move forward onto a square occupied by an enemy piece when another pawn is able to capture to that square.
                        print(f'Illegal move.')
                        raise ValueError
                    else:
                        for move in possible_legal_moves:
                            if move.origin_square[0] == capture_origin_file and move.is_capture():
                                return self.process_move(move)
                        print('Illegal move.')
                        raise ValueError
        else:
            if self.current_position.castling_legal_here(side_to_move, castling):
                back_rank = '1' if side_to_move == 'white' else '8'
                legal_move = LegalMove(color=side_to_move, piece_type='king',
                                       origin_square=f'e{back_rank}',
                                       destination_square=f'g{back_rank}' if castling == 'kingside' else f'c{back_rank}',
                                       castling=castling)
                return self.process_move(legal_move)
            else:
                print('Castling not legal here.')
                raise ValueError

    def show_moves(self) -> None:
        for move in self.moves_record:
            whites_move = self.moves_record[move][0].split(' ', maxsplit=1)[1]
            if len(self.moves_record[move]) == 2:
                blacks_move = self.moves_record[move][1].split(' ', maxsplit=1)[1]
                print(f'{move}. {whites_move} {blacks_move}')
            else:
                print(f'{move}. {whites_move}')

    def restart_game(self) -> None:
        self.current_position = generate_starting_position()
        self.fen_record_dict = {self.current_position.generate_fen().rsplit(' ', maxsplit=2)[0]: 1}
        self.moves_record = {}

    def take_back_last_move(self) -> None:
        if self.moves_record == {}:
            print('Nothing to take back.')
            return
        current_moves = deepcopy(self.moves_record)
        self.restart_game()
        max_move_number = max(list(current_moves.keys()))
        if len(current_moves[max_move_number]) == 2:
            last_move_played = current_moves[max_move_number].pop(1)
        else:
            last_move_played = current_moves[max_move_number][0]
            current_moves.pop(max_move_number)
        if current_moves != {}:
            new_last_move_number = max(list(current_moves.keys()))
            for move_num in range(1, new_last_move_number + 1):
                moves_list = current_moves[move_num]
                whites_move_notation = moves_list[0].rsplit(' ', maxsplit=1)[1]
                self.process_input_notation(whites_move_notation)
                if len(moves_list) == 2:
                    blacks_move_notation = moves_list[1].rsplit(' ', maxsplit=1)[1]
                    self.process_input_notation(blacks_move_notation)
        print(f'{last_move_played} taken back.')







