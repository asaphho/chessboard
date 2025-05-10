from typing import List, Iterable, Dict, Union

from classes.color_position import ColorPosition
from utils.board_functions import scan_qbr_scope, scan_kn_scope, get_intervening_squares, INT_SQUARES_MAP, LINE_EXTEND_MAP, PIECE_MOVE_TYPE_DICT
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


def square_is_around_enemy_king(square: str, opposing_pieces_position: ColorPosition):
    enemy_king_position = opposing_pieces_position.get_king_square()
    squares_around_king = scan_kn_scope('K', enemy_king_position)
    return square in squares_around_king + [enemy_king_position]


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


def detect_battery_or_x_ray(target_sq: str, first_attacking_pns: str, square_piece_dict: Dict[str, str], color: str,
                            x_ray_defense: bool = False) -> List[str]:
    map_key = f'{target_sq}{first_attacking_pns[1:]}'
    pieces = [] if x_ray_defense else [first_attacking_pns]
    line_type = INT_SQUARES_MAP[map_key]['line']
    extended_line = LINE_EXTEND_MAP[map_key]
    for sq in extended_line:
        if sq in square_piece_dict:
            piece = square_piece_dict[sq]
            own_piece = piece.isupper() if color == 'w' else piece.islower()
            if not own_piece or piece.upper() in ('P', 'K', 'N'):
                break
            if line_type not in PIECE_MOVE_TYPE_DICT[piece.upper()]:
                break
            pieces.append(f'{piece.upper()}{sq}')
    return pieces


def is_pinned(king_sq: str, king_color: str, pns: str, target_sq: str, square_piece_dict: Dict[str, str], ignore_target_sq: bool=False) -> Union[str, None]:
    """
    Returns the pinning piece and square (e.g. 'Re1') if the piece indicated by pns (Piece and square it is standing on. e.g. 'Ne5') is unable to move to target_sq because of an absolute pin. False otherwise.
    Note that this will return True only if it attempts to move out of the line of the pin. For example, a rook being pinned along the e-file will still be able to move along the e-file.
    Use only when established that pns and king_sq are in line, and that the movement of pns to target_sq is according to its normal allowed movement type and is not blocked from moving there.
    :param ignore_target_sq: If True, simply returns the pinning piece and square if a pin exists, without regard for the target_sq that the piece is trying to move to.
    :param king_color:
    :param king_sq:
    :param pns:
    :param target_sq:
    :param square_piece_dict:
    :return:
    """
    map_key = f'{king_sq}{pns[1:]}'
    try:
        line_extended = LINE_EXTEND_MAP[map_key]
    except KeyError:
        return None
    squares_between_king_and_pns, line_type = INT_SQUARES_MAP[map_key]['int'], INT_SQUARES_MAP[map_key]['line']
    for int_sq in squares_between_king_and_pns:
        if int_sq in square_piece_dict:
            return None
    for sq in line_extended:
        if sq in square_piece_dict:
            piece_at_square = square_piece_dict[sq]
            if piece_at_square.upper() in ('P', 'K', 'N'):
                return None
            enemy_of_king = piece_at_square.islower() if king_color == 'w' else piece_at_square.isupper()
            if not enemy_of_king:
                return None
            if line_type in PIECE_MOVE_TYPE_DICT[piece_at_square.upper()]:
                if ignore_target_sq or not (target_sq in squares_between_king_and_pns or target_sq in line_extended):
                    return f'{piece_at_square.upper()}{sq}'
                else:
                    return None
    return None


def count_pawns_in_front_on_file(square: str, color: str, square_piece_dict: Dict[str, str]) -> int:
    file = square[0]
    back_rank = 1 if color == 'w' else 8
    if square == f'{file}{back_rank}':
        destination_rank = 9 - back_rank
        direction = 1 if color == 'w' else -1
        squares_in_front = [f'{file}{i}' for i in range(back_rank + direction, destination_rank + direction, direction)]
    else:
        squares_in_front = LINE_EXTEND_MAP[f'{file}1{square}'] if color == 'w' else LINE_EXTEND_MAP[f'{file}8{square}']
    return len([sq for sq in square_piece_dict if sq in squares_in_front and square_piece_dict[sq].upper() == 'P'])


def quick_evaluate(position: Position, bot_params: Dict = None) -> Dict[str, float]:
    params = bot_params if bot_params is not None else {}
    # SCORES FOR SQUARES CONTROLLED BY PAWNS
    central_file_4_th_rank = params.get(0, 0.15)
    central_file_5_th_rank = params.get(1, 0.18)
    central_file_6_th_rank = params.get(2, 0.22)
    bishop_file_4_th_rank = params.get(3, 0.13)
    bishop_file_5_th_rank = params.get(4, 0.15)
    bishop_file_6_th_rank = params.get(5, 0.17)
    seventh_rank = params.get(6, 0.2)
    eighth_rank = params.get(7, 0.23)
    knight_file_5_th_rank = params.get(8, 0.13)
    knight_file_6_th_rank = params.get(9, 0.16)
    all_others = params.get(10, 0.1)

    seventh_rank_scores = {}
    for f in 'abcdefgh':
        seventh_rank_scores[f] = seventh_rank
    eighth_rank_scores = {}
    for f in 'abcdefgh':
        eighth_rank_scores[f] = eighth_rank
    sixth_rank_scores = {'a': all_others, 'b': knight_file_6_th_rank, 'c': bishop_file_6_th_rank,
                         'd': central_file_6_th_rank,
                         'e': central_file_6_th_rank, 'f': bishop_file_6_th_rank, 'g': knight_file_6_th_rank,
                         'h': all_others}
    fifth_rank_scores = {'a': all_others, 'b': knight_file_5_th_rank, 'c': bishop_file_5_th_rank,
                         'd': central_file_5_th_rank,
                         'e': central_file_5_th_rank, 'f': bishop_file_5_th_rank, 'g': knight_file_5_th_rank,
                         'h': all_others}
    fourth_rank_scores = {'a': all_others, 'b': all_others, 'c': bishop_file_4_th_rank, 'd': central_file_4_th_rank,
                          'e': central_file_4_th_rank, 'f': bishop_file_4_th_rank, 'g': all_others, 'h': all_others}
    rank_scores = {'4': fourth_rank_scores, '5': fifth_rank_scores, '6': sixth_rank_scores, '7': seventh_rank_scores,
                   '8': eighth_rank_scores}
    white_pawn_control_scores = {}
    black_pawn_control_scores = {}
    for square in ALL_SQUARES:
        file = square[0]
        rank = square[1]
        if rank in rank_scores:
            white_pawn_control_scores[square] = rank_scores[rank][file]
        else:
            white_pawn_control_scores[square] = all_others

    for square in white_pawn_control_scores:
        rank = int(square[1])
        black_rank = 9 - rank
        mirrored_square = square[0] + str(black_rank)
        black_pawn_control_scores[mirrored_square] = white_pawn_control_scores[square]

    activity_base_score = params.get(11, 0.1)  # BASE SCORE AWARDED FOR EACH SQUARE COVERED BY EACH PIECE (Q, R, B, N)
    central_square_bonus = params.get(12, 0.04)  # ADDITIONAL SCORE AWARDED FOR EACH SQUARE IN e4, d4, e5, or d5 COVERED BY EACH PIECE (Q, R, B, N)
    sixth_rank_piece_control_bonus = params.get(13, 0.04)  # ADDITIONAL SCORE AWARDED FOR EACH SQUARE ON THE SIXTH RANK COVERED BY EACH PIECE (Q, R, B, N)
    square_around_enemy_king = params.get(14, 0.03)  # ADDITIONAL SCORE AWARDED FOR EACH SQUARE AROUND THE ENEMY KING COVERED BY EACH PIECE (Q, R, B, N) OR P
    development_score_penalty = -1 * params.get(15, 0.4)  # APPLIES FOR EACH MINOR PIECE ON ITS HOME SQUARE.
    seventh_rank_bonus = params.get(16, 0.05)  # APPLIES FOR EACH SQUARE A ROOK COVERS THAT IS ON THE SEVENTH RANK.
    centralized_knight_bonus = params.get(17, 0.08)  # FOR KNIGHT ON e4, d4, e5, or d5
    passed_pawn_score = params.get(18, 0.5)
    passed_pawn_advancement_bonus_per_rank = params.get(19, 0.1)
    passed_pawn_advancement_threat_score_per_rank = params.get(20, 0.5)
    rook_semi_open_file_score = params.get(21, 0.08)
    rook_open_file_score = params.get(22, 0.12)
    bishop_pair_score = params.get(23, 0.5)
    pressured_piece_score = params.get(24, 0.08)
    pressured_piece_threat_score = params.get(25, 0.4)
    pinned_piece_threat_score = params.get(26, 0.5)
    pinned_threatened_material_multiplier = 1 + params.get(27, 0.5)
    unique_square_around_enemy_king_score = params.get(28, 0.08)  # ADDITIONAL SCORE FOR EACH UNIQUE SQUARE AROUND THE ENEMY KING CONTROLLED BY ANY PIECE
    unique_square_around_enemy_king_threat_score = params.get(29, 0.4)  # THREAT SCORE FOR EACH UNIQUE SQUARE AROUND THE ENEMY KING CONTROLLED BY ANY PIECE
    supported_queen_around_enemy_king_score = params.get(30, 0.08)  # ADDITIONAL SCORE FOR EACH UNIQUE SQUARE AROUND THE ENEMY KING CONTROLLED BY A QUEEN AND AT LEAST ONE ADDITIONAL PIECE
    supported_queen_around_enemy_king_threat_score = params.get(31, 0.5)  # ADDITIONAL THREAT SCORE FOR EACH UNIQUE SQUARE AROUND THE ENEMY KING CONTROLLED BY A QUEEN AND AT LEAST ONE ADDITIONAL PIECE
    promotion_threat_score = 10 * params.get(32, 0.5)
    base_check_threat_score = 2 * params.get(33, 0.5)
    forced_king_move_threat_score = params.get(34, 0.5)
    forced_free_piece_block_threat_score = 6 * params.get(35, 0.5)
    material_threat_score_factor = params.get(36, 0.5)
    material_threat_simultaneous_with_check = 8 * params.get(37, 0.5)
    overwhelming_material_threat_multiplier = 1 + 2 * params.get(38, 0.5)
    endgame_backward_king_penalty = -1 * params.get(39, 0.4)
    side_to_move = position.to_move()
    side_evaluating_for = opposite_color(side_to_move)
    score = 0
    threat_score = 0
    opposing_material = 0
    for piece in position.get_pieces_by_color(side_to_move).list_unique_piece_types():
        if piece != 'K':
            opposing_material += len(position.get_pieces_by_color(side_to_move).get_piece_type_squares(piece)) * MATERIAL_DICT[piece]
    own_material = 0
    for piece in position.get_pieces_by_color(side_evaluating_for).list_unique_piece_types():
        if piece != 'K':
            own_material += len(position.get_pieces_by_color(side_evaluating_for).get_piece_type_squares(piece)) * MATERIAL_DICT[piece]
    material_difference = own_material - opposing_material
    score += material_difference
    overwhelming_material_multiplier = overwhelming_material_threat_multiplier if opposing_material < 10 and material_difference >= 5 else 1
    is_endgame = own_material < 13 and opposing_material < 13
    threat_contributing_pieces = {}
    square_piece_dict = position.white_pieces.get_square_piece_symbol_dict() | position.black_pieces.get_square_piece_symbol_dict(lowercase=True)
    own_squares_occupied = position.get_pieces_by_color(side_evaluating_for).get_occupied_squares()
    own_king_square = position.get_pieces_by_color(side_evaluating_for).get_king_square()
    opposing_squares_occupied = position.get_pieces_by_color(side_to_move).get_occupied_squares()
    own_piece_covered_square_dict = position.get_piece_scope_dict(side_evaluating_for)
    opposing_piece_covered_square_dict = position.get_piece_scope_dict(side_to_move)
    own_square_covering_piece_dict = invert_piece_scope_dict(own_piece_covered_square_dict)
    opposing_square_covering_piece_dict = invert_piece_scope_dict(opposing_piece_covered_square_dict)
    opposing_king_square = position.get_pieces_by_color(side_to_move).get_king_square()
    check_given = opposing_king_square in own_square_covering_piece_dict
    if check_given:
        threat_score += base_check_threat_score
        potential_escape_squares = [esc_sq for esc_sq in opposing_piece_covered_square_dict[f'K{opposing_king_square}'] if esc_sq not in opposing_squares_occupied and esc_sq not in own_square_covering_piece_dict]
        no_legal_king_move = not any([position.virtual_move_is_legal(VirtualMove(side_to_move, 'K', opposing_king_square, attempt)) for attempt in potential_escape_squares])
        checking_pieces = own_square_covering_piece_dict[opposing_king_square]  # ['Re1', 'Nf6'] (delivering double check on a king on e8)
        double_check = len(checking_pieces) > 1
        if no_legal_king_move and double_check:
            return {'eval': CHECKMATE_SCORE, 'threat': CHECKMATE_SCORE}
        elif double_check:
            threat_score += forced_king_move_threat_score
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
            if not (can_block or can_capture):
                threat_score += forced_king_move_threat_score
            if can_block and no_legal_king_move and not can_capture:
                blocking_convergence = {}
                for pns_dict in legal_blocking_pns:
                    if pns_dict['int'] not in blocking_convergence:
                        blocking_convergence[pns_dict['int']] = [pns_dict['m']]
                    else:
                        blocking_convergence[pns_dict['int']].append(pns_dict['m'])
                if max([len(blocks) for blocks in list(blocking_convergence.values())]) == 1:
                    threat_score += forced_free_piece_block_threat_score
            if no_legal_king_move and not can_block and can_capture:
                if len(legal_capturing_pns) == 1 and checking_piece_square in own_square_covering_piece_dict:
                    checking_piece_worth = MATERIAL_DICT[checking_pieces[0][0]]
                    capturing_piece_worth = MATERIAL_DICT[legal_capturing_pns[0][0]]
                    if (net_gain := capturing_piece_worth - checking_piece_worth) > 0:
                        threat_score += net_gain
    else:
        checking_pieces = []
    own_passed_pawns = {}
    for sq in square_piece_dict:
        piece = square_piece_dict[sq]
        own_piece = piece.isupper() if side_evaluating_for == 'w' else piece.islower()
        color = 'w' if piece.isupper() else 'b'
        if piece.upper() == 'R':
            n_pawns_in_front = count_pawns_in_front_on_file(sq, color, square_piece_dict)
            if n_pawns_in_front == 1:
                score += rook_semi_open_file_score if own_piece else -rook_semi_open_file_score
            elif n_pawns_in_front == 0:
                score += rook_open_file_score if own_piece else -rook_open_file_score
        elif piece.upper() in ('B', 'N'):
            back_rank = '1' if color == 'w' else '8'
            if sq[1] == back_rank:
                score += development_score_penalty if own_piece else -development_score_penalty
            if piece.upper() == 'N':
                if sq in ('e4', 'e5', 'd4', 'd5'):
                    score += centralized_knight_bonus if own_piece else -centralized_knight_bonus
            if piece.upper() == 'B':
                opposing_color = 'w' if piece.islower() else 'b'
                own_color = opposite_color(opposing_color)
                n_bishops = len(position.get_pieces_by_color(own_color).get_piece_type_squares('B'))
                n_opposing_bishops = len(position.get_pieces_by_color(opposing_color).get_piece_type_squares('B'))
                if n_bishops == 2 and n_opposing_bishops == 1:
                    score += bishop_pair_score/2 if own_piece else -bishop_pair_score/2
        elif piece.upper() == 'P':
            n_pawns_in_front = count_pawns_in_front_on_file(sq, color, square_piece_dict)
            if n_pawns_in_front == 0:
                back_rank = '1' if color == 'w' else '8'
                yet_traversed_squares = LINE_EXTEND_MAP[f'{sq[0]}{back_rank}{sq}']
                sq_in_front_attacked = False
                square_covering_piece_dict = opposing_square_covering_piece_dict if own_piece else own_square_covering_piece_dict
                for sq in yet_traversed_squares:
                    if sq in square_covering_piece_dict:
                        if any([pns.startswith('P') for pns in square_covering_piece_dict[sq]]):
                            sq_in_front_attacked = True
                            break
                if not sq_in_front_attacked:
                    score += passed_pawn_score if own_piece else -passed_pawn_score
                    rank = int(sq[1])
                    ranks_advanced = rank - 2 if color == 'w' else (9 - rank) - 2
                    score += ranks_advanced * passed_pawn_advancement_bonus_per_rank if own_piece else -ranks_advanced * passed_pawn_advancement_bonus_per_rank
                    if own_piece:
                        own_passed_pawns[f'P{sq}'] = passed_pawn_score + ranks_advanced * passed_pawn_advancement_bonus_per_rank
                        threat_contributing_pieces[f'P{sq}'] = [ranks_advanced * passed_pawn_advancement_threat_score_per_rank * overwhelming_material_multiplier]
            if own_piece:
                seventh_rank, promotion_rank = (7, 8) if piece == 'P' else (2, 1)
                if int(sq[1]) == seventh_rank:
                    promotion_square = f'{sq[0]}{promotion_rank}'
                    if promotion_square not in opposing_squares_occupied and promotion_square not in opposing_square_covering_piece_dict:
                        threat_contributing_pieces[f'P{sq}'] = [promotion_threat_score * overwhelming_material_multiplier]
                    elif promotion_square not in opposing_squares_occupied and promotion_square in opposing_square_covering_piece_dict:
                        if promotion_square in own_square_covering_piece_dict or detect_battery_or_x_ray(promotion_square, sq, square_piece_dict, side_evaluating_for, True):
                            threat_contributing_pieces[f'P{sq}'] = [promotion_threat_score * overwhelming_material_multiplier]
        elif piece.upper() == 'K' and is_endgame:
            back_rank = '1' if color == 'w' else '8'
            second_rank = '2' if color == 'w' else '7'
            third_rank = '3' if color == 'w' else '6'
            if sq[1] in (back_rank, second_rank):
                score += endgame_backward_king_penalty if own_piece else -endgame_backward_king_penalty
            elif sq[1] == third_rank:
                score += endgame_backward_king_penalty / 2 if own_piece else -endgame_backward_king_penalty / 2

    own_pawn_unique_controlled_squares = []
    already_pawn_controlled_squares_around_king = []
    for pns in own_piece_covered_square_dict:
        piece = pns[0]
        squares_covered = own_piece_covered_square_dict[pns]
        if piece in ('Q', 'R', 'B', 'N'):
            for covered_square in squares_covered:
                score += activity_base_score
                if covered_square in ('e4', 'e5', 'd4', 'd5'):
                    score += central_square_bonus
                if covered_square in opposing_piece_covered_square_dict[f'K{opposing_king_square}'] + [opposing_king_square]:
                    score += square_around_enemy_king
                if piece == 'R':
                    seventh_rank = '7' if side_evaluating_for == 'w' else '2'
                    if covered_square[1] == seventh_rank:
                        score += seventh_rank_bonus
                sixth_rank = '6' if side_evaluating_for == 'w' else '3'
                if covered_square[1] == sixth_rank:
                    score += sixth_rank_piece_control_bonus
        elif piece == 'P':
            pawn_control_score_map = white_pawn_control_scores if side_evaluating_for == 'w' else black_pawn_control_scores
            for covered_square in squares_covered:
                if covered_square not in own_pawn_unique_controlled_squares:
                    score += pawn_control_score_map[covered_square]
                    own_pawn_unique_controlled_squares.append(covered_square)
                else:
                    score += pawn_control_score_map[covered_square] / 2
                if covered_square in opposing_piece_covered_square_dict[f'K{opposing_king_square}'] + [opposing_king_square]:
                    if covered_square not in already_pawn_controlled_squares_around_king:
                        score += square_around_enemy_king
                        already_pawn_controlled_squares_around_king.append(covered_square)

    opposing_pawn_unique_controlled_squares = []
    already_pawn_controlled_squares_around_king = []
    for pns in opposing_piece_covered_square_dict:
        piece = pns[0]
        squares_covered = opposing_piece_covered_square_dict[pns]
        if piece in ('Q', 'R', 'B', 'N'):
            for covered_square in squares_covered:
                score -= activity_base_score
                if covered_square in ('e4', 'e5', 'd4', 'd5'):
                    score -= central_square_bonus
                if covered_square in own_piece_covered_square_dict[f'K{own_king_square}'] + [own_king_square]:
                    score -= square_around_enemy_king
                if piece == 'R':
                    seventh_rank = '7' if side_to_move == 'w' else '2'
                    if covered_square[1] == seventh_rank:
                        score -= seventh_rank_bonus
                sixth_rank = '6' if side_to_move == 'w' else '3'
                if covered_square[1] == sixth_rank:
                    score -= sixth_rank_piece_control_bonus
        elif piece == 'P':
            pawn_control_score_map = white_pawn_control_scores if side_to_move == 'w' else black_pawn_control_scores
            for covered_square in squares_covered:
                if covered_square not in opposing_pawn_unique_controlled_squares:
                    score -= pawn_control_score_map[covered_square]
                    opposing_pawn_unique_controlled_squares.append(covered_square)
                else:
                    score -= pawn_control_score_map[covered_square] / 2
                if covered_square in own_piece_covered_square_dict[f'K{own_king_square}'] + [own_king_square]:
                    if covered_square not in already_pawn_controlled_squares_around_king:
                        score -= square_around_enemy_king
                        already_pawn_controlled_squares_around_king.append(covered_square)

    hanging_material_list = []
    for attacked_square in opposing_square_covering_piece_dict:
        if check_given and not all([pns[1:] == attacked_square for pns in checking_pieces]):
            continue
        if attacked_square in own_squares_occupied or (attacked_square == position.get_en_passant_square() and any([pns[0] == 'P' for pns in opposing_square_covering_piece_dict[attacked_square]])):
            if (attacked_square not in own_pawn_unique_controlled_squares) and attacked_square != position.get_en_passant_square():
                score -= pressured_piece_score
            piece_at_square = square_piece_dict[attacked_square].upper() if attacked_square != position.get_en_passant_square() else 'P'
            if piece_at_square == 'K':
                continue
            if attacked_square not in own_square_covering_piece_dict:
                if attacked_square != position.get_en_passant_square():
                    hanging_material_list.append((f'{piece_at_square}{attacked_square}', MATERIAL_DICT[piece_at_square]))
                else:
                    en_passant_pawn_rank = '4' if side_evaluating_for == 'w' else '5'
                    hanging_material_list.append((f'P{attacked_square[0]}{en_passant_pawn_rank}', 1))
            else:
                defenders_pns = own_square_covering_piece_dict[attacked_square]
                defenders_array = []
                for pns in defenders_pns:
                    if is_pinned(own_king_square, side_evaluating_for, pns, attacked_square, square_piece_dict):
                        continue
                    curr_battery = [pns]
                    if pns[0] in ('K', 'N'):
                        defenders_array.append(curr_battery)
                        continue
                    defender_sq = pns[1:]
                    if f'{attacked_square}{defender_sq}' in INT_SQUARES_MAP:
                        battery = detect_battery_or_x_ray(attacked_square, pns, square_piece_dict, side_evaluating_for)
                        curr_battery = []
                        for battery_pns in battery:
                            if is_pinned(own_king_square, side_evaluating_for, battery_pns, attacked_square, square_piece_dict):
                                break
                            curr_battery.append(battery_pns)
                        if curr_battery:
                            defenders_array.append(curr_battery)
                attackers_pns = opposing_square_covering_piece_dict[attacked_square]
                attackers_array = []
                for pns in attackers_pns:
                    if is_pinned(opposing_king_square, side_to_move, pns, attacked_square, square_piece_dict):
                        continue
                    if pns[0] in ('K', 'N'):
                        attackers_array.append([pns])
                        continue
                    attacker_square = pns[1:]
                    if f'{attacked_square}{attacker_square}' in INT_SQUARES_MAP:
                        battery = detect_battery_or_x_ray(attacked_square, pns, square_piece_dict, side_to_move)
                        curr_battery = []
                        for battery_pns in battery:
                            if is_pinned(opposing_king_square, side_to_move, battery_pns, attacked_square, square_piece_dict):
                                break
                            curr_battery.append(battery_pns)
                        if curr_battery:
                            attackers_array.append(curr_battery)
                        x_ray = detect_battery_or_x_ray(attacked_square, pns, square_piece_dict, side_evaluating_for, True)
                        curr_battery = [f'A{pns}']
                        for battery_pns in x_ray:
                            if is_pinned(own_king_square, side_evaluating_for, battery_pns, attacked_square, square_piece_dict):
                                break
                            curr_battery.append(battery_pns)
                        if len(curr_battery) > 1:
                            defenders_array.append(curr_battery)
                if (not defenders_array) and len(attackers_array) > 0:
                    if attacked_square != position.get_en_passant_square():
                        hanging_material_list.append((f'{piece_at_square}{attacked_square}', MATERIAL_DICT[piece_at_square]))
                    else:
                        en_passant_pawn_rank = '4' if side_evaluating_for == 'w' else '5'
                        hanging_material_list.append((f'P{attacked_square[0]}{en_passant_pawn_rank}', 1))
                    continue
                if not attackers_array:
                    continue
                defenders_array.sort(key=lambda x: 101 if x[0][0] == 'A' else MATERIAL_DICT[x[0][0]])
                attackers_array.sort(key=lambda x: MATERIAL_DICT[x[0][0]])
                curr_material_change = 0
                piece_on_exchange_square = piece_at_square
                attacker_capture = True
                while len(defenders_array) > 0 and len(attackers_array) > 0:
                    if attacker_capture:
                        capturing_pns = attackers_array[0].pop(0)
                        curr_material_change -= MATERIAL_DICT[piece_on_exchange_square]
                        piece_on_exchange_square = capturing_pns[0]
                        attackers_array = list(filter(lambda x: len(x) > 0, attackers_array))
                        attackers_array.sort(key=lambda x: MATERIAL_DICT[x[0][0]])
                        for i in range(len(defenders_array)):
                            if defenders_array[i][0] == f'A{capturing_pns}':
                                defenders_array[i].pop(0)
                                break
                        defenders_array.sort(key=lambda x: 101 if x[0][0] == 'A' else MATERIAL_DICT[x[0][0]])
                        attacker_capture = not attacker_capture
                        if curr_material_change > 0:
                            break
                    else:
                        if defenders_array[0][0].startswith('A'):
                            break
                        capturing_pns = defenders_array[0].pop(0)
                        curr_material_change += MATERIAL_DICT[piece_on_exchange_square]
                        piece_on_exchange_square = capturing_pns[0]
                        defenders_array = list(filter(lambda x: len(x) > 0, defenders_array))
                        defenders_array.sort(key=lambda x: 101 if x[0][0] == 'A' else MATERIAL_DICT[x[0][0]])
                        attacker_capture = not attacker_capture
                        if curr_material_change < 0:
                            break
                if len(attackers_array) > 0 and attacker_capture and len(defenders_array) == 0:
                    curr_material_change -= MATERIAL_DICT[piece_on_exchange_square]
                elif len(defenders_array) > 0 and not attacker_capture and len(attackers_array) == 0:
                    if not defenders_array[0][0].startswith('A'):
                        curr_material_change += MATERIAL_DICT[piece_on_exchange_square]
                if curr_material_change < 0:
                    if attacked_square != position.get_en_passant_square():
                        hanging_material_list.append((f'{piece_at_square}{attacked_square}', -curr_material_change))
                    else:
                        en_passant_pawn_rank = '4' if side_evaluating_for == 'w' else '5'
                        hanging_material_list.append((f'P{attacked_square[0]}{en_passant_pawn_rank}', -curr_material_change))
    score -= max([m[1] for m in hanging_material_list]) if hanging_material_list else 0

    for attacked_square in own_square_covering_piece_dict:
        if attacked_square in opposing_squares_occupied:
            if attacked_square == opposing_king_square:
                continue
            if attacked_square not in opposing_pawn_unique_controlled_squares:
                threat_score += pressured_piece_threat_score
                score += pressured_piece_threat_score
            capturing_pns = own_square_covering_piece_dict[attacked_square]
            lightest_capturing_pns = min(capturing_pns, key=lambda x: MATERIAL_DICT[x[0]])
            piece_at_square = square_piece_dict[attacked_square].upper()
            pinning_pns = is_pinned(opposing_king_square, side_to_move, f'{piece_at_square}{attacked_square}', '', square_piece_dict, ignore_target_sq=True)
            if pinning_pns:
                if pinning_pns in threat_contributing_pieces:
                    threat_contributing_pieces[pinning_pns].append(pinned_piece_threat_score)
                else:
                    threat_contributing_pieces[pinning_pns] = [pinned_piece_threat_score]
            if attacked_square not in opposing_square_covering_piece_dict:
                if lightest_capturing_pns not in threat_contributing_pieces:
                    threat_contributing_pieces[lightest_capturing_pns] = [MATERIAL_DICT[piece_at_square] * material_threat_score_factor]
                else:
                    threat_contributing_pieces[lightest_capturing_pns].append(MATERIAL_DICT[piece_at_square] * material_threat_score_factor)
            else:
                capturing_piece_worth = MATERIAL_DICT[lightest_capturing_pns[0]]
                threatened_material = MATERIAL_DICT[piece_at_square] - capturing_piece_worth
                if threatened_material > 0:
                    m = pinned_threatened_material_multiplier if pinning_pns else 1
                    if lightest_capturing_pns not in threat_contributing_pieces:
                        threat_contributing_pieces[lightest_capturing_pns] = [threatened_material * material_threat_score_factor * m]
                    else:
                        threat_contributing_pieces[lightest_capturing_pns].append(threatened_material * material_threat_score_factor * m)
                    if check_given and not all([pns == lightest_capturing_pns for pns in checking_pieces]):
                        threat_score += material_threat_simultaneous_with_check

    for hanging_pns, m in hanging_material_list:
        if hanging_pns in threat_contributing_pieces:
            threat_contributing_pieces.pop(hanging_pns)
        if hanging_pns in own_passed_pawns:
            score -= own_passed_pawns.pop(hanging_pns)
    for pns in threat_contributing_pieces:
        threat_score += sum(threat_contributing_pieces[pns])

    for square in opposing_piece_covered_square_dict[f'K{opposing_king_square}']:
        if square in own_square_covering_piece_dict:
            threat_score += unique_square_around_enemy_king_threat_score * overwhelming_material_multiplier
            score += unique_square_around_enemy_king_score
            if any([pns.startswith('Q') for pns in own_square_covering_piece_dict[square]]):
                queen_pns = [pns for pns in own_square_covering_piece_dict[square] if pns[0] == 'Q'][0]
                battery = detect_battery_or_x_ray(square, queen_pns, square_piece_dict, color='w' if side_evaluating_for == 'w' else 'b')
                if len(own_square_covering_piece_dict[square]) > 1 or len(battery) > 1:
                    threat_score += supported_queen_around_enemy_king_threat_score * overwhelming_material_multiplier
                    score += supported_queen_around_enemy_king_score

    for square in own_piece_covered_square_dict[f'K{own_king_square}']:
        if square in opposing_square_covering_piece_dict:
            score -= unique_square_around_enemy_king_score
            if any([pns.startswith('Q') for pns in opposing_square_covering_piece_dict[square]]):
                queen_pns = [pns for pns in opposing_square_covering_piece_dict[square] if pns[0] == 'Q'][0]
                battery = detect_battery_or_x_ray(square, queen_pns, square_piece_dict, color='w' if side_to_move == 'w' else 'b')
                if len(opposing_square_covering_piece_dict[square]) > 1 or len(battery) > 1:
                    score -= supported_queen_around_enemy_king_score

    return {'eval': score, 'threat': threat_score}
