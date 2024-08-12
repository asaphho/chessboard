from typing import List, Iterable, Dict

from classes.color_position import ColorPosition
from utils.board_functions import scan_qbr_scope, scan_kn_scope, get_intervening_squares, INT_SQUARES_MAP
from classes.move import LegalMove, VirtualMove
from classes.position import Position, opposite_color
from simple_bot.utils import branch_from_position, check_if_move_ends_game

SYMBOL_TO_PIECE = {'P': 'pawn', 'K': 'king', 'Q': 'queen', 'R': 'rook', 'B': 'bishop', 'N': 'knight'}
MATERIAL_DICT = {'K': 10, 'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}
ALL_SQUARES = []
for f in 'abcdefgh':
    for r in '12345678':
        ALL_SQUARES.append(f + r)

# CHECKMATE SCORE
CHECKMATE_SCORE = 999999

# SCORES FOR SQUARES CONTROLLED BY PAWNS
CENTRAL_FILE_4TH_RANK = 0.18
CENTRAL_FILE_5TH_RANK = 0.21
CENTRAL_FILE_6TH_RANK = 0.23
BISHOP_FILE_4TH_RANK = 0.16
BISHOP_FILE_5TH_RANK = 0.18
BISHOP_FILE_6TH_RANK = 0.21
SEVENTH_RANK = 0.23
EIGHTH_RANK = 0.28
KNIGHT_FILE_5TH_RANK = 0.16
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
ACTIVITY_COUNT_MULTIPLIER = 0.08  # BASE
CENTRAL_SQUARE_BONUS = 0.06
SQUARE_AROUND_ENEMY_KING = 0.06

# MATERIAL THREAT MULTIPLIER
MATERIAL_THREAT_MULTIPLIER = 0.2
CHECKMATE_THREAT_SCORE = 5

# DEVELOPMENT SCORE PENALTY
DEVELOPMENT_SCORE_PENALTY = -0.4

# SEVENTH RANK BONUS
SEVENTH_RANK_BONUS = 0.08

# CENTRALIZED KNIGHT BONUS
CENTRALIZED_KNIGHT_BONUS = 0.08


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


def calculate_threat_score(position: Position, side_just_moved: str, include_mate_threat: bool = False) -> float:
    attacked_color = opposite_color(side_just_moved)
    copy_position = position.copy()
    attacked_colors_pieces = copy_position.get_pieces_by_color(attacked_color)
    copy_position.change_side_to_move()
    copy_position.remove_en_passant_square()
    attacked_colors_king_sq = attacked_colors_pieces.get_king_square()
    all_legal_moves = copy_position.get_all_legal_moves_for_side_to_move()
    all_material_gaining_moves = [move for move in all_legal_moves if (move.is_capture() and move.destination_square != attacked_colors_king_sq) or move.pawn_promotion_required()]
    threat_score = 0
    checkmate_threat_score = 0
    if not position.is_under_check(attacked_color) and include_mate_threat:
        for move in all_legal_moves:
            if check_if_move_ends_game(copy_position, move) == 'checkmate':
                checkmate_threat_score += CHECKMATE_THREAT_SCORE
    for move in all_material_gaining_moves:
        if not move.pawn_promotion_required():
            captured_piece = copy_position.look_at_square(move.destination_square).upper()
            gain = MATERIAL_DICT[captured_piece]
            new_position = branch_from_position(copy_position, move)
            capturing_piece_worth = MATERIAL_DICT[move.piece_moved]
            possible_recaptures = [mv for mv in new_position.get_all_legal_moves_for_side_to_move() if mv.is_capture() and mv.destination_square == move.destination_square]
            if possible_recaptures:
                if (net_gain := gain - capturing_piece_worth) > 0:
                    threat_score += net_gain
            else:
                threat_score += gain
        elif not move.is_capture():
            new_position = branch_from_position(position, move)
            possible_captures = [mv for mv in new_position.get_all_legal_moves_for_side_to_move() if mv.is_capture() and mv.destination_square == move.destination_square]
            if not possible_captures:
                threat_score += MATERIAL_DICT[move.promotion_piece] - 1
        else:
            captured_piece = copy_position.look_at_square(move.destination_square).upper()
            net_gain = MATERIAL_DICT[captured_piece] + MATERIAL_DICT[move.promotion_piece] - 1
            new_position = branch_from_position(copy_position, move)
            possible_recaptures = [mv for mv in new_position.get_all_legal_moves_for_side_to_move() if mv.is_capture() and mv.destination_square == move.destination_square]
            if possible_recaptures:
                net_gain -= MATERIAL_DICT[move.promotion_piece]
            threat_score += net_gain
    return (threat_score * MATERIAL_THREAT_MULTIPLIER if not position.is_under_check(position.to_move()) else threat_score * MATERIAL_THREAT_MULTIPLIER * 1.5) + checkmate_threat_score


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


def development_score(position: Position, side_evaluating_for: str) -> int:
    """
    gives DEVELOPMENT SCORE PENALTY for each minor piece on back rank. Should be zero or negative.
    :param position:
    :param side_evaluating_for:
    :return:
    """
    back_rank = '1' if side_evaluating_for == 'w' else '8'
    score = 0
    pieces_positions = position.get_pieces_by_color(side_evaluating_for)
    for piece in pieces_positions.list_unique_piece_types():
        if piece == 'N' or piece == 'B':
            squares = pieces_positions.get_piece_type_squares(piece)
            for sq in squares:
                if sq[1] == back_rank:
                    score += DEVELOPMENT_SCORE_PENALTY
    return score


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
    score += calculate_threat_score(position, side_evaluating_for)
    score += development_score(position, side_evaluating_for) - development_score(position, side_to_move)
    return score


def evaluate_exchange_on_square(position: Position, square: str, initiating_capture: LegalMove) -> int:
    """
    Counts the amount of material that the side to move stands to gain from initiating a series of captures and
    recaptures on the given square. Both sides "dogpile" onto the square, sending their least valuable pieces to capture
    first, until one side cannot recapture.
    :param initiating_capture:
    :param square:
    :param position:
    :return:
    """

    if not initiating_capture.is_en_passant_capture():
        captured_piece = position.look_at_square(square).upper()
    else:
        captured_piece = 'P'
    position_after_capture = branch_from_position(position, initiating_capture)
    possible_recaptures = position_after_capture.scan_all_captures_to_square(square)
    material_gain = MATERIAL_DICT[captured_piece]
    if not possible_recaptures:
        return material_gain
    else:
        recapture = min(possible_recaptures, key=lambda x: MATERIAL_DICT[x.piece_moved])
        return material_gain - evaluate_exchange_on_square(position_after_capture, square, recapture)


def find_material_hanging_on_square(position: Position, capture: LegalMove) -> int:
    square_captured_on = capture.destination_square
    if position.get_en_passant_square() != square_captured_on:
        first_capturable_piece = position.look_at_square(square_captured_on).upper()
    else:
        first_capturable_piece = 'P'
    cost = MATERIAL_DICT[capture.piece_moved]
    worth = MATERIAL_DICT[first_capturable_piece]
    material_gain = evaluate_exchange_on_square(position, square_captured_on, capture)
    if material_gain == worth:
        return material_gain
    elif material_gain <= worth - cost and worth > cost:
        return worth - cost
    elif 0 < material_gain <= worth <= cost:
        return material_gain
    elif cost > worth and material_gain >= worth:
        return worth
    return 0


def new_evaluate(position: Position) -> Dict[str, float]:
    side_to_move = position.to_move()
    side_evaluating_for = opposite_color(side_to_move)
    score = 0
    threat_score = 0
    position_with_pass_move = position.copy()
    position_with_pass_move.change_side_to_move()
    position_with_pass_move.remove_en_passant_square()
    square_piece_dict = position.white_pieces.get_square_piece_symbol_dict() | position.black_pieces.get_square_piece_symbol_dict(lowercase=True)
    all_legal_moves_in_position = position.get_all_legal_moves_for_side_to_move()
    if not all_legal_moves_in_position:
        if position.is_under_check(side_to_move):
            return {'eval': CHECKMATE_SCORE, 'threat': CHECKMATE_SCORE}
        else:
            return {'eval': 0, 'threat': 0}
    all_legal_moves_in_pass_position = position_with_pass_move.get_all_legal_moves_for_side_to_move()

    for sq in square_piece_dict:
        piece = square_piece_dict[sq]
        if piece.isupper():
            score += MATERIAL_DICT[piece] if side_evaluating_for == 'w' else -MATERIAL_DICT[piece]
        else:
            score += MATERIAL_DICT[piece.upper()] if side_evaluating_for == 'b' else -MATERIAL_DICT[piece.upper()]
        back_rank = '1' if side_evaluating_for == 'w' else '8'
        enemy_back_rank = '1' if side_evaluating_for == 'b' else '1'
        minor_pieces = ('b', 'n', 'B', 'N')
        if piece in minor_pieces:
            own_minor_piece = (piece.isupper() and side_evaluating_for == 'w') or \
                              (piece.islower() and side_evaluating_for == 'b')
            score += DEVELOPMENT_SCORE_PENALTY if sq[1] == back_rank and own_minor_piece else 0
            score -= DEVELOPMENT_SCORE_PENALTY if sq[1] == enemy_back_rank and not own_minor_piece else 0
            if piece in ('n', 'N'):
                score += CENTRALIZED_KNIGHT_BONUS if own_minor_piece and sq in ('e4', 'e5', 'e4', 'd5') else 0
                score -= CENTRALIZED_KNIGHT_BONUS if not own_minor_piece and sq in ('e4', 'e5', 'd4', 'd5') else 0
        if piece in ('p', 'P'):
            if piece == 'p':
                squares_controlled = position.scan_pawn_attacked_squares('b', sq)
                for controlled_square in squares_controlled:
                    score += BLACK_PAWN_CONTROL_SCORES[controlled_square] if side_evaluating_for == 'b' else -BLACK_PAWN_CONTROL_SCORES[controlled_square]
            else:
                squares_controlled = position.scan_pawn_attacked_squares('w', sq)
                for controlled_square in squares_controlled:
                    score += WHITE_PAWN_CONTROL_SCORES[controlled_square] if side_evaluating_for == 'w' else -WHITE_PAWN_CONTROL_SCORES[controlled_square]

    lightest_piece_captures_in_reply = {}
    for mv in all_legal_moves_in_position:
        if mv.piece_moved in ('Q', 'R', 'B', 'N'):
            score -= ACTIVITY_COUNT_MULTIPLIER
            if mv.destination_square in ('e4', 'd4', 'e5', 'd5'):
                score -= CENTRAL_SQUARE_BONUS
            if mv.piece_moved == 'R':
                score -= SEVENTH_RANK_BONUS if (side_evaluating_for == 'w' and mv.destination_square[1] == '2') or\
                                               (side_evaluating_for == 'b' and mv.destination_square[1] == '7') \
                    else 0
        if mv.piece_moved != 'K':
            if square_around_enemy_king(mv.destination_square, position.get_pieces_by_color(side_evaluating_for)):
                score -= SQUARE_AROUND_ENEMY_KING
        if mv.is_capture():
            destination_sq = mv.destination_square
            if destination_sq not in lightest_piece_captures_in_reply:
                lightest_piece_captures_in_reply[destination_sq] = mv
            else:
                existing_mv = lightest_piece_captures_in_reply[destination_sq]
                if MATERIAL_DICT[mv.piece_moved] < MATERIAL_DICT[existing_mv.piece_moved]:
                    lightest_piece_captures_in_reply[destination_sq] = mv

    hanging_material = [0]
    for capturable_square in lightest_piece_captures_in_reply:
        capture = lightest_piece_captures_in_reply[capturable_square]
        hanging_material.append(find_material_hanging_on_square(position, capture))
    score -= max(hanging_material)

    lightest_threatened_piece_captures = {}
    enemy_king_position = position.get_pieces_by_color(side_to_move).get_king_square()
    under_check = position.is_under_check(side_to_move)
    for mv in all_legal_moves_in_pass_position:
        if mv.destination_square == enemy_king_position:
            continue
        if not under_check:
            if check_if_move_ends_game(position_with_pass_move, mv) == 'checkmate':
                threat_score += CHECKMATE_THREAT_SCORE
        if mv.piece_moved in ('Q', 'R', 'B', 'N'):
            score += ACTIVITY_COUNT_MULTIPLIER
            if mv.destination_square in ('e4', 'd4', 'e5', 'd5'):
                score += CENTRAL_SQUARE_BONUS
            if mv.piece_moved == 'R':
                score += SEVENTH_RANK_BONUS if (side_evaluating_for == 'w' and mv.destination_square[1] == '7') or\
                                               (side_evaluating_for == 'b' and mv.destination_square[1] == '2') \
                    else 0
        if mv.piece_moved != 'K':
            if square_around_enemy_king(mv.destination_square, position.get_pieces_by_color(side_to_move)):
                score += SQUARE_AROUND_ENEMY_KING
        if mv.is_capture():
            if mv.destination_square not in lightest_threatened_piece_captures:
                lightest_threatened_piece_captures[mv.destination_square] = mv
            else:
                existing_mv = lightest_threatened_piece_captures[mv.destination_square]
                if MATERIAL_DICT[mv.piece_moved] < MATERIAL_DICT[existing_mv.piece_moved]:
                    lightest_threatened_piece_captures[mv.destination_square] = mv

    for threatened_capture_square in lightest_threatened_piece_captures:
        threatened_capture = lightest_threatened_piece_captures[threatened_capture_square]
        material_threat = find_material_hanging_on_square(position_with_pass_move, threatened_capture)
        threat_score += material_threat * MATERIAL_THREAT_MULTIPLIER
        score += material_threat * MATERIAL_THREAT_MULTIPLIER
    return {'eval': score, 'threat': threat_score}


def invert_piece_scope_dict(piece_scope_dict: Dict[str, List[str]]) -> Dict[str, List[str]]:
    square_covering_piece_dict = {}
    for piece_n_square in piece_scope_dict:
        covered_squares = piece_scope_dict[piece_n_square]
        for square in covered_squares:
            if square not in square_covering_piece_dict:
                square_covering_piece_dict[square] = [piece_n_square]
            else:
                square_covering_piece_dict[square].append(piece_n_square)
    return square_covering_piece_dict


def quick_evaluate(position: Position) -> Dict[str, float]:
    side_to_move = position.to_move()
    side_evaluating_for = opposite_color(side_to_move)
    score = 0
    threat_score = 0
    square_piece_dict = position.white_pieces.get_square_piece_symbol_dict() | position.black_pieces.get_square_piece_symbol_dict(lowercase=True)
    own_squares_occupied = position.get_pieces_by_color(side_evaluating_for).get_occupied_squares()
    own_king_square = position.get_pieces_by_color(side_evaluating_for).get_king_square()
    opposing_squares_occupied = position.get_pieces_by_color(side_to_move).get_occupied_squares()
    own_piece_covered_square_dict = position.get_piece_scope_dict(side_evaluating_for)
    opposing_piece_covered_square_dict = position.get_piece_scope_dict(side_to_move)
    own_square_covering_piece_dict = invert_piece_scope_dict(own_piece_covered_square_dict)
    opposing_square_covering_piece_dict = invert_piece_scope_dict(opposing_piece_covered_square_dict)
    opposing_king_square = position.get_pieces_by_color(side_to_move).get_king_square()
    is_under_check = opposing_king_square in own_square_covering_piece_dict
    if is_under_check:
        potential_escape_squares = [esc_sq for esc_sq in opposing_piece_covered_square_dict[f'K{opposing_king_square}'] if esc_sq not in opposing_squares_occupied and esc_sq not in own_square_covering_piece_dict]
        no_legal_king_move = not any([position.virtual_move_is_legal(VirtualMove(side_to_move, 'K', opposing_king_square, attempt)) for attempt in potential_escape_squares])
        checking_pieces = own_square_covering_piece_dict[opposing_king_square]  # ['Re1', 'Nf6'] (delivering double check on a king on e8)
        double_check = len(checking_pieces) > 1
        if no_legal_king_move and double_check:
            return {'eval': CHECKMATE_SCORE, 'threat': CHECKMATE_SCORE}
        elif double_check:
            threat_score += 3
        else:
            checking_piece_square = checking_pieces[0][1:]
            if checking_piece_square not in opposing_square_covering_piece_dict:
                can_capture = False
                legal_capturing_pns = []
            else:
                potential_capturing_piece_n_squares = opposing_square_covering_piece_dict[checking_piece_square]
                legal_capturing_pns = [pns for pns in potential_capturing_piece_n_squares if position.virtual_move_is_legal(VirtualMove(side_to_move, pns[0], pns[1:], checking_piece_square))]
                can_capture = len(legal_capturing_pns) > 0
            if f'{checking_piece_square}{opposing_king_square}' not in INT_SQUARES_MAP:
                legal_blocking_pns = []
                can_block = False
            else:
                intervening_squares = INT_SQUARES_MAP[f'{checking_piece_square}{opposing_king_square}']['int']
                legal_blocking_pns = []
                for int_sq in intervening_squares:
                    if int_sq in opposing_square_covering_piece_dict:
                        potential_blocking_pns = opposing_square_covering_piece_dict[int_sq]
                        legal_blocking_pns.extend([{'pns': pns, 'int': int_sq, 'm': MATERIAL_DICT[pns[0]]} for pns in potential_blocking_pns if position.virtual_move_is_legal(VirtualMove(side_to_move, pns[0], pns[1:], int_sq)) and pns[0] not in ('P', 'K')])
                    pawns_on_same_file = [pns for pns in opposing_piece_covered_square_dict if pns[0] == 'P' and pns[1] == int_sq[0]]
                    for pns in pawns_on_same_file:
                        squares_it_can_move_to = position.scan_pawn_non_capture_moves(side_to_move, pns[1:])
                        if int_sq in squares_it_can_move_to:
                            is_legal = position.virtual_move_is_legal(VirtualMove(side_to_move, 'P', pns[1:], int_sq))
                            if is_legal:
                                legal_blocking_pns.append({'pns': pns, 'int': int_sq, 'm': 1})
                can_block = len(legal_blocking_pns) > 0
            if no_legal_king_move and (not can_capture) and (not can_block):
                return {'eval': CHECKMATE_SCORE, 'threat': CHECKMATE_SCORE}
            if can_block and no_legal_king_move and not can_capture:
                blocking_convergence = {}
                for pns_dict in legal_blocking_pns:
                    if pns_dict['int'] not in blocking_convergence:
                        blocking_convergence[pns_dict['int']] = [pns_dict['m']]
                    else:
                        blocking_convergence[pns_dict['int']].append(pns_dict['m'])
                if max([len(blocks) for blocks in list(blocking_convergence.values())]) == 1:
                    threat_score += 3
            if no_legal_king_move and not can_block and can_capture:
                if len(legal_capturing_pns) == 1 and checking_piece_square in own_square_covering_piece_dict:
                    checking_piece_worth = MATERIAL_DICT[checking_pieces[0][0]]
                    capturing_piece_worth = MATERIAL_DICT[legal_capturing_pns[0][0]]
                    if (net_gain := capturing_piece_worth - checking_piece_worth) > 0:
                        threat_score += net_gain

    for sq in square_piece_dict:
        piece = square_piece_dict[sq]
        own_piece = piece.isupper() if side_evaluating_for == 'w' else piece.islower()
        score += MATERIAL_DICT[piece.upper()] if own_piece else -MATERIAL_DICT[piece.upper()]
        if piece.upper() in ('B', 'N'):
            back_rank = '1' if piece.isupper() else '8'
            if sq[1] == back_rank:
                score += DEVELOPMENT_SCORE_PENALTY if own_piece else -DEVELOPMENT_SCORE_PENALTY
            if piece.upper() == 'N':
                if sq in ('e4', 'e5', 'd4', 'd5'):
                    score += CENTRALIZED_KNIGHT_BONUS if own_piece else -CENTRALIZED_KNIGHT_BONUS

    for pns in own_piece_covered_square_dict:
        piece = pns[0]
        squares_covered = own_piece_covered_square_dict[pns]
        if piece in ('Q', 'R', 'B', 'N'):
            for covered_square in squares_covered:
                score += ACTIVITY_COUNT_MULTIPLIER
                if covered_square in ('e4', 'e5', 'd4', 'd5'):
                    score += CENTRAL_SQUARE_BONUS
                if covered_square in opposing_piece_covered_square_dict[f'K{opposing_king_square}'] + [opposing_king_square]:
                    score += SQUARE_AROUND_ENEMY_KING
                if piece == 'R':
                    seventh_rank = '7' if side_evaluating_for == 'w' else '2'
                    if covered_square[1] == seventh_rank:
                        score += SEVENTH_RANK_BONUS
        elif piece == 'P':
            pawn_control_score_map = WHITE_PAWN_CONTROL_SCORES if side_evaluating_for == 'w' else BLACK_PAWN_CONTROL_SCORES
            already_controlled_squares = []
            already_controlled_squares_around_king = []
            for covered_square in squares_covered:
                if covered_square not in already_controlled_squares:
                    score += pawn_control_score_map[covered_square]
                    already_controlled_squares.append(covered_square)
                else:
                    score += pawn_control_score_map[covered_square] / 2
                if covered_square in opposing_piece_covered_square_dict[f'K{opposing_king_square}'] + [opposing_king_square]:
                    if covered_square not in already_controlled_squares_around_king:
                        score += SQUARE_AROUND_ENEMY_KING
                        already_controlled_squares_around_king.append(covered_square)

    for pns in opposing_piece_covered_square_dict:
        piece = pns[0]
        squares_covered = opposing_piece_covered_square_dict[pns]
        if piece in ('Q', 'R', 'B', 'N'):
            for covered_square in squares_covered:
                score -= ACTIVITY_COUNT_MULTIPLIER
                if covered_square in ('e4', 'e5', 'd4', 'd5'):
                    score -= CENTRAL_SQUARE_BONUS
                if covered_square in own_piece_covered_square_dict[f'K{own_king_square}'] + [own_king_square]:
                    score -= SQUARE_AROUND_ENEMY_KING
                if piece == 'R':
                    seventh_rank = '7' if side_to_move == 'w' else '2'
                    if covered_square[1] == seventh_rank:
                        score -= SEVENTH_RANK_BONUS
        elif piece == 'P':
            pawn_control_score_map = WHITE_PAWN_CONTROL_SCORES if side_to_move == 'w' else BLACK_PAWN_CONTROL_SCORES
            already_controlled_squares = []
            already_controlled_squares_around_king = []
            for covered_square in squares_covered:
                if covered_square not in already_controlled_squares:
                    score -= pawn_control_score_map[covered_square]
                    already_controlled_squares.append(covered_square)
                else:
                    score -= pawn_control_score_map[covered_square] / 2
                if covered_square in own_piece_covered_square_dict[f'K{own_king_square}'] + [own_king_square]:
                    if covered_square not in already_controlled_squares_around_king:
                        score -= SQUARE_AROUND_ENEMY_KING
                        already_controlled_squares_around_king.append(covered_square)

    hanging_material_list = []
    for attacked_square in opposing_square_covering_piece_dict:
        if attacked_square in own_squares_occupied:
            piece_at_square = square_piece_dict[attacked_square].upper()
            if attacked_square not in own_square_covering_piece_dict:
                hanging_material_list.append(MATERIAL_DICT[piece_at_square])
            else:
                capturing_pieces_pns = opposing_square_covering_piece_dict[attacked_square]
                capturing_piece_worth = min([MATERIAL_DICT[pns[0]] for pns in capturing_pieces_pns])
                hanging_material = MATERIAL_DICT[piece_at_square] - capturing_piece_worth
                if hanging_material > 0:
                    hanging_material_list.append(hanging_material)
    score -= max(hanging_material_list) if hanging_material_list else 0

    for attacked_square in own_square_covering_piece_dict:
        if attacked_square in opposing_squares_occupied:
            if attacked_square == opposing_king_square:
                continue
            piece_at_square = square_piece_dict[attacked_square].upper()
            if attacked_square not in opposing_square_covering_piece_dict:
                threat_score += MATERIAL_DICT[piece_at_square]
            else:
                capturing_pns = own_square_covering_piece_dict[attacked_square]
                capturing_piece_worth = min([MATERIAL_DICT[pns[0]] for pns in capturing_pns])
                threatened_material = MATERIAL_DICT[piece_at_square] - capturing_piece_worth
                if threatened_material > 0:
                    threat_score += threatened_material

    return {'eval': score, 'threat': threat_score}
