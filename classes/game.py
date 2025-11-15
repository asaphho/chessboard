import json
from typing import Union, Tuple

from classes.bot import Bot
from classes.position import generate_starting_position, Position
from classes.move import LegalMove
from utils.parse_notation import check_for_castling, find_piece_moved_and_destination_square,\
    check_for_disambiguating_string, piece_to_symbol, check_for_promotion_piece, pawn_capture_origin_file
from copy import deepcopy


class Game:
    """
        A class for managing the state and logic of a chess game.

        This class acts as a game controller and supports:
            - Applying and validating player and engine moves.
            - Tracking move history and FEN repetition.
            - Detecting game-ending conditions (checkmate, stalemate, repetition, 50-move rule, insufficient material).
            - Handling algebraic input notation and move disambiguation.
            - Undoing moves and restarting the game.
            - Playing moves using a chess bot.

        Attributes:
            current_position (Position): The current position of the game.
            fen_record_dict (dict): Dictionary tracking the occurrence count of FEN states for repetition detection.
            moves_record (dict): Dictionary mapping move numbers to SAN strings of moves played.
            starting_position (Position): The initial position when the game began.
        """

    def __init__(self, starting_position: Position = None):
        """
            Initializes a new game from a given starting position or from the standard starting position.

            Args:
                starting_position (Position, optional): If provided, sets the game to start from this position.
            """
        self.current_position = generate_starting_position() if starting_position is None else starting_position
        self.fen_record_dict = {self.current_position.generate_fen().rsplit(' ', maxsplit=2)[0]: 1}
        self.moves_record = {}
        self.starting_position = self.current_position.copy()

    def process_move(self, legal_move: LegalMove, return_move_for_gui: bool = False, opening_book_path: str = None) -> Union[str, Tuple[str, LegalMove]]:
        """
            Applies a legal move to the game, updates internal state, tracks repetition, and optionally records it to an opening book.

            Args:
                legal_move (LegalMove): The move to process.
                return_move_for_gui (bool): If True, return the move object and SAN string for GUI use.
                opening_book_path (str, optional): Path to the opening book file to update.

            Returns:
                str or (str, LegalMove): Notation of the move, or a tuple with the notation and LegalMove.
            """
        side_that_moved = legal_move.color
        move_number = self.current_position.get_move_number()
        fen_before_move = self.current_position.generate_fen().rsplit(' ', maxsplit=2)[0]
        move_notation = self.current_position.process_legal_move(legal_move)
        current_fen = self.current_position.generate_fen()
        current_fen_for_record = current_fen.rsplit(' ', maxsplit=2)[0]
        if current_fen_for_record in self.fen_record_dict:
            self.fen_record_dict[current_fen_for_record] += 1
        else:
            self.fen_record_dict[current_fen_for_record] = 1
        if side_that_moved == 'w':
            self.moves_record[move_number] = [move_notation]
        elif move_number not in self.moves_record:
            self.moves_record[move_number] = [f'{move_number}. ...', move_notation]
        else:
            self.moves_record[move_number].append(move_notation)

        if opening_book_path:
            uci = legal_move.generate_uci()
            with open(opening_book_path, 'r') as readfile:
                curr_opening_book = json.load(readfile)
            if fen_before_move not in curr_opening_book:
                curr_opening_book[fen_before_move] = [uci]
            elif uci not in curr_opening_book[fen_before_move]:
                curr_opening_book[fen_before_move].append(uci)
            with open(opening_book_path, 'w') as writefile:
                writefile.write(json.dumps(curr_opening_book, indent=3))

        return (move_notation, legal_move) if return_move_for_gui else move_notation

    def drawn_by_repetition(self) -> bool:
        """
            Determines whether the game is drawn due to threefold repetition.

            Returns:
                bool: True if the same position has occurred three times.
            """
        return any([self.fen_record_dict[fen] >= 3 for fen in self.fen_record_dict])

    def drawn_by_50_move_rule(self) -> bool:
        """
            Determines whether the 50-move rule applies.

            Returns:
                bool: True if 50 full moves have passed with no pawn movement or captures.
            """
        return self.current_position.get_half_move_clock() >= 100

    def drawn_by_reduction(self) -> bool:
        """
            Determines whether the game is drawn due to insufficient mating material.

            Returns:
                bool: True if neither side has sufficient material to checkmate.
            """
        white_pieces = self.current_position.white_pieces
        black_pieces = self.current_position.black_pieces
        unique_white_pieces = white_pieces.list_unique_piece_types()
        unique_black_pieces = black_pieces.list_unique_piece_types()
        if any([piece in ('Q', 'R', 'P') for piece in unique_white_pieces + unique_black_pieces]):
            return False
        if any([len(piece_list) >= 3 for piece_list in [unique_white_pieces, unique_black_pieces]]):
            return False
        if unique_black_pieces == ['K'] and unique_white_pieces == ['K']:
            return True
        if 'B' in unique_white_pieces and 'N' not in unique_white_pieces:
            white_insufficient_material = len(white_pieces.get_piece_type_squares('B')) == 1
            white_has_minor_piece = True
        elif 'N' in unique_white_pieces and 'B' not in unique_white_pieces:
            white_insufficient_material = len(white_pieces.get_piece_type_squares('N')) == 1
            white_has_minor_piece = True
        else:
            white_insufficient_material = True
            white_has_minor_piece = False
        if not white_insufficient_material:
            return False
        if 'B' in unique_black_pieces and 'N' not in unique_black_pieces:
            black_insufficient_material = len(black_pieces.get_piece_type_squares('B')) == 1
            black_has_minor_piece = True
        elif 'N' in unique_black_pieces and 'B' not in unique_black_pieces:
            black_insufficient_material = len(black_pieces.get_piece_type_squares('N')) == 1
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
        """
            Checks for game-ending conditions: checkmate, stalemate, repetition, 50-move rule, or insufficient material.

            Returns:
                str: A message describing the outcome, or 'N' if the game should continue.
            """
        side_to_move = self.current_position.to_move()
        legal_moves_available = self.current_position.get_all_legal_moves_for_side_to_move()
        if len(legal_moves_available) == 0:
            if self.current_position.is_under_check(side_to_move):
                if side_to_move == 'w':
                    return 'Black wins by checkmate.'
                else:
                    return 'White wins by checkmate.'
            else:
                return 'Drawn by stalemate.'

        if self.drawn_by_repetition():
            return 'Drawn by repetition.'
        if self.drawn_by_50_move_rule():
            return 'Drawn by 50-move rule.'
        if self.drawn_by_reduction():
            return 'Drawn by reduction.'
        return 'N'

    def process_input_notation(self, notation_str: str, return_move_for_gui: bool = False, opening_book_path: str = None) -> Union[str, Tuple[str, LegalMove]]:
        """
            Parses and validates a move given in standard algebraic notation, disambiguates if needed,
            applies the move if legal.

            Args:
                notation_str (str): The move in algebraic notation (e.g. 'Nf3', 'exd5', 'O-O').
                return_move_for_gui (bool): If True, returns the move along with notation.
                opening_book_path (str, optional): Path to record move in opening book.

            Returns:
                str or (str, LegalMove): The move in notation format, or a tuple with notation and move object.

            Raises:
                ValueError: If the move is illegal or ambiguous.
            """
        side_to_move = self.current_position.to_move()
        castling = check_for_castling(notation_str)
        if castling == 'N':
            piece_moved, destination_square = find_piece_moved_and_destination_square(notation_str)
            all_legal_moves = self.current_position.get_all_legal_moves_for_color(side_to_move)
            possible_legal_moves = [move for move in all_legal_moves if move.piece_moved == piece_moved]
            if len(possible_legal_moves) == 0:
                raise ValueError('Illegal move')
            possible_legal_moves = [move for move in possible_legal_moves if move.destination_square == destination_square]
            if len(possible_legal_moves) == 0:
                raise ValueError('Illegal move')
            elif piece_moved != 'P':
                disambiguating_string = check_for_disambiguating_string(notation_str, destination_square,
                                                                        piece_to_symbol(piece_moved))
                if disambiguating_string == '' and len(possible_legal_moves) > 1:
                    raise ValueError(f'Ambiguity detected. More than one {piece_moved} can move to {destination_square}.')
                elif disambiguating_string == '' and len(possible_legal_moves) == 1:
                    return self.process_move(possible_legal_moves[0], return_move_for_gui, opening_book_path)
                elif len(disambiguating_string) == 1 and disambiguating_string.isalpha():
                    possible_legal_moves = [move for move in possible_legal_moves if move.origin_square[0] == disambiguating_string]
                    if len(possible_legal_moves) > 1:
                        raise ValueError(f'Ambiguity detected. More than one {piece_moved} can reach {destination_square} from the {disambiguating_string}-file.')
                    elif len(possible_legal_moves) == 0:
                        raise ValueError(f'No {piece_moved} on {disambiguating_string}-file able to move to {destination_square}.')
                    else:
                        return self.process_move(possible_legal_moves[0], return_move_for_gui, opening_book_path)
                elif len(disambiguating_string) == 1 and disambiguating_string.isnumeric():
                    possible_legal_moves = [move for move in possible_legal_moves if move.origin_square[1] == disambiguating_string]
                    if len(possible_legal_moves) > 1:
                        raise ValueError(f'Ambiguity detected. More than one {piece_moved} on rank {disambiguating_string} can reach {destination_square}.')
                    elif len(possible_legal_moves) == 0:
                        raise ValueError(f'No {piece_moved} able to move to {destination_square} from rank {disambiguating_string}.')
                    else:
                        return self.process_move(possible_legal_moves[0], return_move_for_gui, opening_book_path)
                elif len(disambiguating_string) == 2:
                    possible_legal_moves = [move for move in possible_legal_moves if move.origin_square == disambiguating_string]
                    if len(possible_legal_moves) == 0:
                        raise ValueError(f'No {piece_moved} on {disambiguating_string} to move to {destination_square}.')
                    else:
                        return self.process_move(possible_legal_moves[0], return_move_for_gui, opening_book_path)
                else:
                    raise ValueError(f'Something went wrong: Unhandled disambiguation string {disambiguating_string}.')
            else:
                promotion_rank = '1' if side_to_move == 'b' else '8'
                if destination_square[1] == promotion_rank:
                    promotion_piece = check_for_promotion_piece(notation_str, destination_square)
                    if promotion_piece == 'None':
                        raise ValueError(f'Promotion piece required as pawn has reached last rank. Add Q, R, B, or N right after the destination square.')
                    capture_origin_file = pawn_capture_origin_file(notation_str, destination_square)
                    if capture_origin_file == '':
                        for move in possible_legal_moves:
                            if move.promotion_piece == promotion_piece and not move.is_capture():
                                return self.process_move(move, return_move_for_gui, opening_book_path)
                        raise ValueError('Something went wrong. Pawn reached last rank but no pawn promotion LegalMove objects found to match promotion piece.')
                    else:
                        for move in possible_legal_moves:
                            if move.origin_square[0] == capture_origin_file and move.promotion_piece == promotion_piece and move.is_capture():
                                return self.process_move(move, return_move_for_gui, opening_book_path)
                        raise ValueError('Something went wrong. Pawn reached last rank but no pawn promotion LegalMove objects found to match promotion piece.')
                else:
                    capture_origin_file = pawn_capture_origin_file(notation_str, destination_square)
                    if capture_origin_file == '':
                        for move in possible_legal_moves:
                            if not move.is_capture():
                                return self.process_move(move, return_move_for_gui, opening_book_path)
                        # code can reach here in the case of a pawn attempting to move forward onto a square occupied by an enemy piece when another pawn is able to capture to that square.
                        raise ValueError('Illegal move.')
                    else:
                        for move in possible_legal_moves:
                            if move.origin_square[0] == capture_origin_file and move.is_capture():
                                return self.process_move(move, return_move_for_gui, opening_book_path)
                        raise ValueError('Illegal move.')
        else:
            if self.current_position.castling_legal_here(side_to_move, castling):
                back_rank = '1' if side_to_move == 'w' else '8'
                legal_move = LegalMove(color=side_to_move, piece_type='K',
                                       origin_square=f'e{back_rank}',
                                       destination_square=f'g{back_rank}' if castling == 'k' else f'c{back_rank}',
                                       castling=castling)
                return self.process_move(legal_move, return_move_for_gui, opening_book_path)
            else:
                raise ValueError(f'Castling {castling}-side not legal here.')

    def show_moves(self, return_string_for_window: bool = False) -> Union[str, None]:
        """
            Displays or returns the move history in a readable format.

            Args:
                return_string_for_window (bool): If True, returns the move list as a string.

            Returns:
                str or None: Move list string (if requested), or prints to console.
            """
        ret_str = '' if return_string_for_window else None
        move_numbers = list(self.moves_record.keys())
        if not move_numbers:
            if return_string_for_window:
                return ''
            else:
                print('')
                return
        first_move = min(move_numbers)
        last_move = max(move_numbers)
        for move in range(first_move, last_move + 1):
            whites_move = self.moves_record[move][0].split(' ', maxsplit=1)[1]
            if len(self.moves_record[move]) == 2:
                blacks_move = self.moves_record[move][1].split(' ', maxsplit=1)[1]
                line = f'{move}. {whites_move} {blacks_move}'
            else:
                line = f'{move}. {whites_move}'
            if not return_string_for_window:
                print(line)
            else:
                ret_str += f'{line}\n'
        return ret_str

    def restart_game(self) -> None:
        """
            Resets the game to the initial starting position.
            """
        self.current_position = self.starting_position.copy()
        self.fen_record_dict = {self.current_position.generate_fen().rsplit(' ', maxsplit=2)[0]: 1}
        self.moves_record = {}

    def take_back_last_move(self, silent: bool = False) -> Union[None, str]:
        """
            Rewinds the game by one move, restoring the previous position.

            Args:
                silent (bool): If True, returns message instead of printing.

            Returns:
                str or None: Message describing the undone move, or None if printed directly.
            """
        flipped = self.current_position.is_flipped()
        if self.moves_record == {}:
            if not silent:
                print('Nothing to take back.')
                return
            else:
                return 'Nothing to take back.'
        current_moves = deepcopy(self.moves_record)
        self.restart_game()
        if flipped:
            self.current_position.flip_position()
        min_move_number = min(list(current_moves.keys()))
        max_move_number = max(list(current_moves.keys()))
        if len(current_moves[max_move_number]) == 2:
            last_move_played = current_moves[max_move_number].pop(1)
        else:
            last_move_played = current_moves[max_move_number][0]
            current_moves.pop(max_move_number)
        if current_moves != {}:
            new_last_move_number = max(list(current_moves.keys()))
            for move_num in range(min_move_number, new_last_move_number + 1):
                moves_list = current_moves[move_num]
                whites_move_notation = moves_list[0].rsplit(' ', maxsplit=1)[1]
                self.process_input_notation(whites_move_notation)
                if len(moves_list) == 2:
                    blacks_move_notation = moves_list[1].rsplit(' ', maxsplit=1)[1]
                    self.process_input_notation(blacks_move_notation)
        if not silent:
            print(f'{last_move_played} taken back.')
        else:
            return f'{last_move_played} taken back.'

    def play_computer_move(self, bot: Bot, return_move_for_gui: bool = False) -> Union[str, Tuple[str, LegalMove]]:
        """
            Plays the best move for the current side using the given bot.

            Args:
                bot (Bot): The bot instance used to generate a move.
                return_move_for_gui (bool): If True, also return the LegalMove object.

            Returns:
                str or (str, LegalMove): The SAN string of the bot's move, or a tuple with notation and move object.
            """
        legal_moves = self.current_position.get_all_legal_moves_for_side_to_move()
        best_move_uci = bot.make_move(self.current_position)
        try:
            origin_square, destination_square = best_move_uci[:2], best_move_uci[2:4]
        except Exception:
            current_fen = self.current_position.generate_fen().rsplit(' ', maxsplit=2)[0]
            bot.remove_bad_uci(current_fen, best_move_uci)
            return self.play_computer_move(bot=bot, return_move_for_gui=return_move_for_gui)
        if len(best_move_uci) == 5:
            promotion_piece = best_move_uci[-1].upper()
        else:
            promotion_piece = ''
        if promotion_piece:
            for move in legal_moves:
                if move.origin_square == origin_square and move.destination_square == destination_square and move.promotion_piece == promotion_piece:
                    return self.process_move(move, return_move_for_gui)
        else:
            for move in legal_moves:
                if move.origin_square == origin_square and move.destination_square == destination_square:
                    return self.process_move(move, return_move_for_gui)

        current_fen = self.current_position.generate_fen().rsplit(' ', maxsplit=2)[0]
        bot.remove_bad_uci(current_fen, best_move_uci)
        return self.play_computer_move(bot=bot, return_move_for_gui=return_move_for_gui)
