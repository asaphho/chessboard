from typing import List, Iterable

from classes.color_position import ColorPosition
from utils.board_functions import scan_qbr_scope, scan_kn_scope, get_intervening_squares
from classes.move import LegalMove
from classes.position import Position, opposite_color
from simple_bot.utils import branch_from_position

SYMBOL_TO_PIECE = {'P': 'pawn', 'K': 'king', 'Q': 'queen', 'R': 'rook', 'B': 'bishop', 'N': 'knight'}
MATERIAL_DICT = {'K': 10, 'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}
ALL_SQUARES = []
for f in 'abcdefgh':
    for r in '12345678':
        ALL_SQUARES.append(f + r)

# CHECKMATE SCORE
CHECKMATE_SCORE = 999999

# SCORES FOR SQUARES CONTROLLED BY PAWNS
CENTRAL_FILE_4TH_RANK = 0.2
CENTRAL_FILE_5TH_RANK = 0.22
CENTRAL_FILE_6TH_RANK = 0.24
BISHOP_FILE_4TH_RANK = 0.18
BISHOP_FILE_5TH_RANK = 0.20
BISHOP_FILE_6TH_RANK = 0.22
SEVENTH_RANK = 0.25
EIGHTH_RANK = 0.3
KNIGHT_FILE_5TH_RANK = 0.15
KNIGHT_FILE_6TH_RANK = 0.18
ALL_OTHERS = 0.1

SEVENTH_RANK_SCORES = {}
for f in 'abcdefgh':
    SEVENTH_RANK_SCORES[f] = SEVENTH_RANK
EIGHTH_RANK_SCORES = {}
for f in 'abcdefgh':
    EIGHTH_RANK_SCORES[f] = EIGHTH_RANK
SIXTH_RANK_SCORES = {'a': ALL_OTHERS, 'b': KNIGHT_FILE_6TH_RANK, 'c': BISHOP_FILE_6TH_RANK, 'd': CENTRAL_FILE_6TH_RANK,
                     'e': CENTRAL_FILE_6TH_RANK, 'f': BISHOP_FILE_6TH_RANK, 'g': KNIGHT_FILE_6TH_RANK, 'h': ALL_OTHERS}
FIFTH_RANK_SCORES = {'a': ALL_OTHERS, 'b': KNIGHT_FILE_5TH_RANK, 'c': BISHOP_FILE_5TH_RANK, 'd': CENTRAL_FILE_5TH_RANK,
                     'e': CENTRAL_FILE_5TH_RANK, 'f': BISHOP_FILE_5TH_RANK, 'g': KNIGHT_FILE_5TH_RANK, 'h': ALL_OTHERS}
FOURTH_RANK_SCORES = {'a': ALL_OTHERS, 'b': ALL_OTHERS, 'c': BISHOP_FILE_4TH_RANK, 'd': CENTRAL_FILE_4TH_RANK,
                      'e': CENTRAL_FILE_4TH_RANK, 'f': BISHOP_FILE_4TH_RANK, 'g': ALL_OTHERS, 'h': ALL_OTHERS}
RANK_SCORES = {'4': FOURTH_RANK_SCORES, '5': FIFTH_RANK_SCORES, '6': SIXTH_RANK_SCORES, '7': SEVENTH_RANK_SCORES, '8': EIGHTH_RANK_SCORES}
WHITE_PAWN_CONTROL_SCORES = {}
BLACK_PAWN_CONTROL_SCORES = {}
for square in ALL_SQUARES:
    file = square[0]
    rank = square[1]
    if rank in RANK_SCORES:
        WHITE_PAWN_CONTROL_SCORES[square] = RANK_SCORES[rank][file]
    else:
        WHITE_PAWN_CONTROL_SCORES[square] = ALL_OTHERS

for square in WHITE_PAWN_CONTROL_SCORES:
    rank = int(square[1])
    black_rank = 9 - rank
    mirrored_square = square[0] + str(black_rank)
    BLACK_PAWN_CONTROL_SCORES[mirrored_square] = WHITE_PAWN_CONTROL_SCORES[square]

# MULTIPLIER FOR NUMBER OF LEGAL PIECE MOVES AVAILABLE
LEGAL_PIECE_MOVE_MULTIPLIER = 0.1

# ACTIVITY MULTIPLIER
ACTIVITY_COUNT_MULTIPLIER = 0.12  # BASE
CENTRAL_SQUARE_BONUS = 0.15
SQUARE_AROUND_ENEMY_KING = 0.25

# MATERIAL THREAT MULTIPLIER
MATERIAL_THREAT_MULTIPLIER = 0.5


def count_material(position: Position, color: str) -> int:
    """
    Counts the number of pawns worth of material on the given side in the given position
    :param position:
    :param color: 'w' or 'b'
    :return:
    """
    pieces = position.get_pieces_by_color(color)
    piece_types = pieces.list_unique_piece_types()
    total = 0
    for piece_type in piece_types:
        number_of_pieces_of_type = len(pieces.get_piece_type_squares(piece_type))
        total += number_of_pieces_of_type * MATERIAL_DICT[piece_type]
    return total


def count_material_imbalance(position: Position, color: str) -> int:
    """
    Calculates the material imbalance in favor of the given color in the given position.
    :param position:
    :param color: 'w' or 'b'.
    :return: e.g. returning 3 if color='w' means that white is up 3 pawns of material
    """
    own_material = count_material(position, color)
    opponents_material = count_material(position, opposite_color(color))
    return own_material - opponents_material


def evaluate_exchange_square(position: Position, square: str, init_possible_captures: List[LegalMove]) -> int:
    """
    Counts the amount of material that the side to move stands to gain from initiating a series of captures and
    recaptures on the given square. Both sides "dogpile" onto the square, sending their least valuable pieces to capture
    first, until one side cannot recapture.
    :param init_possible_captures:
    :param square:
    :param position:
    :return:
    """
    capturing_move = min(init_possible_captures, key=lambda x: MATERIAL_DICT[x.piece_moved])
    if not capturing_move.is_en_passant_capture():
        captured_piece = position.look_at_square(square).upper()
    else:
        captured_piece = 'P'
    position_after_capture = branch_from_position(position, capturing_move)
    possible_recaptures = [move for move in position_after_capture.get_all_legal_moves_for_side_to_move() if
                           move.destination_square == square and move.is_capture()]
    material_gain = MATERIAL_DICT[captured_piece]
    if not possible_recaptures:
        return material_gain
    else:
        return material_gain - evaluate_exchange_square(position_after_capture, square, possible_recaptures)


def calculate_material_threat_score(position: Position, side_just_moved: str) -> float:
    attacked_color = opposite_color(side_just_moved)
    copy_position = position.copy()
    attacked_colors_pieces = copy_position.get_pieces_by_color(attacked_color)
    copy_position.change_side_to_move()
    copy_position.remove_en_passant_square()
    attacked_colors_king_sq = attacked_colors_pieces.get_king_square()
    all_captures = [move for move in copy_position.get_all_legal_moves_for_side_to_move() if move.is_capture() and move.destination_square != attacked_colors_king_sq]
    material_threat_score = 0
    for capture in all_captures:
        captured_piece = copy_position.look_at_square(capture.destination_square).upper()
        gain = MATERIAL_DICT[captured_piece]
        new_position = branch_from_position(copy_position, capture)
        capturing_piece_worth = MATERIAL_DICT[capture.piece_moved]
        possible_recaptures = [move for move in new_position.get_all_legal_moves_for_side_to_move() if move.is_capture() and move.destination_square == capture.destination_square]
        if possible_recaptures:
            if (net_gain := gain - capturing_piece_worth) > 0:
                material_threat_score += net_gain
        else:
            material_threat_score += gain
    return material_threat_score * MATERIAL_THREAT_MULTIPLIER if not position.is_under_check(position.to_move()) else material_threat_score * MATERIAL_THREAT_MULTIPLIER * 3


def find_hanging_material(position: Position) -> List[int]:
    all_possible_captures = [move for move in position.get_all_legal_moves_for_side_to_move() if move.is_capture()]
    capture_squares = [move.destination_square for move in all_possible_captures]
    material_gains = [0]
    for square in capture_squares:
        possible_captures = [move for move in all_possible_captures if move.destination_square == square]
        if position.get_en_passant_square() != square:
            first_capturable_piece = position.look_at_square(square).upper()
        else:
            first_capturable_piece = 'P'
        cost = min([MATERIAL_DICT[move.piece_moved] for move in possible_captures])
        worth = MATERIAL_DICT[first_capturable_piece]
        material_gain = evaluate_exchange_square(position, square, possible_captures)
        if material_gain == worth:
            material_gains.append(material_gain)
        elif material_gain <= worth - cost and worth > cost:
            material_gains.append(worth - cost)
        elif worth <= cost and material_gain > 0:
            material_gains.append(material_gain)

    return material_gains


def all_legal_piece_moves(position: Position, color: str) -> List[LegalMove]:
    """
    Returns all the legal piece moves (knight, bishop, rook, or queen) in the given position with the given color to
    move
    :param position:
    :param color: 'w' or 'b'
    :return:
    """
    all_legal_moves = position.get_all_legal_moves_for_color(color)
    legal_piece_moves = [move for move in all_legal_moves if move.piece_moved in ('R', 'Q', 'B', 'N')]
    return legal_piece_moves


def square_around_enemy_king(square: str, opposing_pieces_position: ColorPosition):
    enemy_king_position = opposing_pieces_position.get_king_square()
    squares_around_king = scan_kn_scope('K', enemy_king_position)
    return square in squares_around_king + [enemy_king_position]


def get_piece_activity_score(position: Position, color: str) -> float:
    score = 0
    own_pieces = position.get_pieces_by_color(color)
    opposing_pieces = position.get_pieces_by_color(opposite_color(color))
    occupied_squares = position.get_occupied_squares()

    def is_central_square(sq):
        return sq in ('e4', 'd4', 'e5', 'd5')

    def calculate_activity_multiplier(square, opposing_pieces_position):
        multiplier = ACTIVITY_COUNT_MULTIPLIER
        if square_around_enemy_king(square, opposing_pieces_position):
            multiplier += SQUARE_AROUND_ENEMY_KING
        if is_central_square(square):
            multiplier += CENTRAL_SQUARE_BONUS
        return multiplier

    for piece_type in own_pieces.list_unique_piece_types():
        if piece_type in ('Q', 'B', 'R'):
            for from_square in own_pieces.get_piece_type_squares(piece_type):
                scope = scan_qbr_scope(piece_type, from_square)
                for line_type in scope:
                    for candidate_square in scope[line_type]:
                        intervening_squares = get_intervening_squares(from_square, candidate_square, line_type)
                        blocked = any([sq in occupied_squares for sq in intervening_squares])
                        if not blocked:
                            score += calculate_activity_multiplier(candidate_square, opposing_pieces)
        elif piece_type == 'N':
            for from_square in own_pieces.get_piece_type_squares(piece_type):
                scope = scan_kn_scope(piece_type, from_square)
                for sq in scope:
                    if sq not in own_pieces.get_occupied_squares():
                        score += calculate_activity_multiplier(sq, opposing_pieces)
    return score


def squares_controlled_by_pawns(position: Position, color: str) -> List[str]:
    """
    Returns all the squares attacked by pawns (ignoring any pins) by the given color in the given position.
    :param position:
    :param color: 'w' or 'b'
    :return: the set of all squares attacked by white pawns if color='w'. Pins are ignored.
    """
    squares_attacked = []
    squares_with_pawns = position.get_pieces_by_color(color).get_piece_type_squares('P')
    for square in squares_with_pawns:
        squares_attacked.extend(position.scan_pawn_attacked_squares(color, square))
    return squares_attacked


def get_pawn_control_score(controlled_squares: List[str], color: str, opposing_pieces: ColorPosition) -> float:
    """
    Gets the score of the given color in a position from the squares it attacks by its pawns.
    :param opposing_pieces:
    :param controlled_squares: The output of squares_controlled_by_pawns
    :param color: 'w' or 'b'
    :return: the total score
    """
    total = 0
    for sq in controlled_squares:
        total += WHITE_PAWN_CONTROL_SCORES[sq] if color == 'w' else BLACK_PAWN_CONTROL_SCORES[sq]
        total += SQUARE_AROUND_ENEMY_KING if square_around_enemy_king(sq, opposing_pieces) else 0
    return total


def piece_moves_reduced_by_enemy_pawn_control(unreduced_piece_moves: List[str],
                                              squares_controlled: Iterable[str]) -> List[str]:
    """
    Returns the subset of unreduced_piece_moves that do not put a piece on a square controlled by an enemy pawn
    (pins are ignored).
    :param unreduced_piece_moves: The piece moves (knight, bishop, rook, queen) in the current position of one
    side
    :param squares_controlled: An iterable containing all the squares attacked by enemy pawns in the same position
    :return:
    """
    return [sq for sq in unreduced_piece_moves if sq not in squares_controlled]


def evaluate(position: Position) -> float:
    """
    The evaluation function to be called to evaluate how good or bad a position is for the side that has just moved.
    :param position: Position object
    :return: float. The higher, the better. 0 means equal position.
    """
    side_to_move = position.to_move()
    side_evaluating_for = opposite_color(side_to_move)
    if not position.get_all_legal_moves_for_color(side_to_move):
        if position.is_under_check(side_to_move):
            return CHECKMATE_SCORE
        else:
            return 0
    score = count_material_imbalance(position, side_evaluating_for)  # MATERIAL IMBALANCE
    own_pawn_controlled_squares = squares_controlled_by_pawns(position, side_evaluating_for)
    opposing_pawn_controlled_squares = squares_controlled_by_pawns(position, side_to_move)
    activity = get_piece_activity_score(position, side_evaluating_for)
    opposing_activity = get_piece_activity_score(position, side_to_move)
    score += activity - opposing_activity  # PIECE ACTIVITY
    score += get_pawn_control_score(own_pawn_controlled_squares, side_evaluating_for,
                                    position.get_pieces_by_color(side_to_move)) - \
             get_pawn_control_score(opposing_pawn_controlled_squares, side_to_move,
                                    position.get_pieces_by_color(side_evaluating_for))  # SQUARES CONTROLLED BY PAWNS
    score -= max(find_hanging_material(position))
    score += calculate_material_threat_score(position, side_evaluating_for)
    return score