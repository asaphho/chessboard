from typing import Tuple, List, Dict

LETTER_TO_NUM = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8}
NUM_TO_LETTER = {}
for letter in LETTER_TO_NUM:
    NUM_TO_LETTER[LETTER_TO_NUM[letter]] = letter

ALL_SQUARES = []
files = 'abcdefgh'
ranks = '12345678'
for f in files:
    for r in ranks:
        ALL_SQUARES.append(f'{f}{r}')


def square_color_int(square: str) -> int:
    """

    :param square: str e.g. 'e5'
    :return: int 0 for light square, 1 for dark square
    """
    file = LETTER_TO_NUM[square[0]]
    rank = int(square[1])
    return int((file % 2) == (rank % 2))


def square_to_coordinate(square: str) -> str:
    file = square[0]
    file_num = LETTER_TO_NUM[file]
    rank = square[1]
    return f'{file_num}{rank}'


def coordinate_to_square(coordinate: str) -> str:
    file = NUM_TO_LETTER[int(coordinate[0])]
    return f'{file}{coordinate[1]}'


def check_squares_in_line(square1: str, square2: str) -> str:
    if square1 == square2:
        print(f"Cannot move from {square1} to {square2} as they are the same square.")
        raise ValueError
    file_diff, rank_diff = get_rank_and_file_diffs(square1, square2)
    if file_diff > 0 and rank_diff == 0:
        return 'r'
    elif file_diff == 0 and rank_diff > 0:
        return 'f'
    elif file_diff == rank_diff:
        return 'd'
    else:
        return 'N'


def get_rank_and_file_diffs(square1: str, square2: str) -> Tuple[int, int]:
    coordinate1 = square_to_coordinate(square1)
    coordinate2 = square_to_coordinate(square2)
    file_diff = get_rank_or_file_diff(coordinate1, coordinate2, 'file')
    rank_diff = get_rank_or_file_diff(coordinate1, coordinate2, 'rank')
    return file_diff, rank_diff


def get_rank_or_file_diff(coordinate1: str, coordinate2: str, dimension: str) -> int:
    return abs(int(coordinate1[0 if dimension == 'file' else 1]) - int(coordinate2[0 if dimension == 'file' else 1]))


def is_knight_move(square1: str, square2: str) -> bool:
    diff_tuple = get_rank_and_file_diffs(square1, square2)
    return (diff_tuple == (2, 1)) or (diff_tuple == (1, 2))


def get_intervening_squares(square1: str, square2: str, line_type: str) -> List[str]:
    def make_range(start, end):
        if end > start:
            return range(start + 1, end)
        elif end < start:
            return range(start - 1, end, -1)
    rank1 = int(square1[1])
    rank2 = int(square2[1])
    file1 = LETTER_TO_NUM[square1[0]]
    file2 = LETTER_TO_NUM[square2[0]]
    if line_type == 'f':
        if abs(rank1 - rank2) <= 1:
            return []
        squares = [f'{NUM_TO_LETTER[file1]}{rank}' for rank in make_range(rank1, rank2)]
    elif line_type == 'r':
        if abs(file1 - file2) <= 1:
            return []
        squares = [f"{NUM_TO_LETTER[file]}{rank1}" for file in make_range(file1, file2)]
    elif line_type == 'd':
        if abs(rank1 - rank2) <= 1:
            return []
        files = list(make_range(file1, file2))
        ranks = list(make_range(rank1, rank2))
        squares = [f"{NUM_TO_LETTER[files[i]]}{ranks[i]}" for i in range(len(files))]
    else:
        print(f'Unrecognized line type: {line_type}')
        raise ValueError
    return squares


def scan_rook_scope(from_square: str) -> Dict[str, List[str]]:
    """
    All the squares a rook can reach in one move from input from_square on an empty board.
    :param from_square: e.g. 'e5'
    :return: if input from_square='e5', returns {'f': ['e1', 'e2', 'e3', 'e4', 'e6', 'e7', 'e8'], 'r': ['a5', 'b5', 'c5', 'd5', 'f5', 'g5', 'h5']}
    """
    rook_scope = {'f': [], 'r': []}
    origin_file, origin_rank = from_square[0], from_square[1]
    for f in 'abcdefgh'.replace(origin_file, ''):
        rook_scope['r'].append(f'{f}{origin_rank}')
    for r in '12345678'.replace(origin_rank, ''):
        rook_scope['f'].append(f'{origin_file}{r}')
    return rook_scope


def scan_bishop_scope(from_square: str) -> Dict[str, List[str]]:
    """
    All the squares a bishop can reach in one move from input from_square on an empty board.
    :param from_square: e.g. 'd3'
    :return: if from_square='d3', returns squares in a dictionary of the following form: {'d': ['b1', 'c2', 'e4', 'f5', 'g6', 'h7', 'c4', 'b5', 'a6', 'e2', 'f1']}. The list order may not be the same.
    """
    bishop_scope = {'d': []}
    from_coordinate = square_to_coordinate(from_square)
    file_int = int(from_coordinate[0])
    rank_int = int(from_coordinate[1])
    for i in range(1, 8):
        file = file_int + i
        rank = rank_int + i
        if file <= 8 and rank <= 8:
            bishop_scope['d'].append(coordinate_to_square(f'{file}{rank}'))
        file = file_int + i
        rank = rank_int - i
        if file <= 8 and rank >= 1:
            bishop_scope['d'].append(coordinate_to_square(f'{file}{rank}'))
        file = file_int - i
        rank = rank_int + i
        if file >= 1 and rank <= 8:
            bishop_scope['d'].append(coordinate_to_square(f'{file}{rank}'))
        file = file_int - i
        rank = rank_int - i
        if file >= 1 and rank >= 1:
            bishop_scope['d'].append(coordinate_to_square(f'{file}{rank}'))
    return bishop_scope


def scan_queen_scope(from_square: str) -> Dict[str, List[str]]:
    """
    Returns all the squares a queen can move to in one move from input from_square on an empty board.
    :param from_square: e.g. 'h5'
    :return: {'f': ['h1', 'h2', ...], 'r': ['a5', 'b5', ...], 'd': ['d1', 'e2', ...]}
    """
    return scan_rook_scope(from_square) | scan_bishop_scope(from_square)


def scan_king_scope(from_square: str) -> List[str]:
    """
    Returns the list of all the squares around from_square.
    :param from_square: e.g. 'd6'
    :return: if from_square='d6', returns ['c5', 'c6', 'c7', 'd5', 'd7', 'e5', 'e6', 'e7']
    """
    from_coordinate = square_to_coordinate(from_square)
    file_int = int(from_coordinate[0])
    rank_int = int(from_coordinate[1])
    king_scope = []
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            if i == 0 and j == 0:
                continue
            file = file_int + i
            rank = rank_int + j
            if 1 <= file <= 8 and 1 <= rank <= 8:
                king_scope.append(coordinate_to_square(f'{file}{rank}'))
    return king_scope


def scan_knight_scope(from_square: str) -> List[str]:
    """
    Returns the squares that a knight can reach in one move from input from_square on an empty board.
    :param from_square: e.g. 'f3'
    :return: if from_square='f3', returns, not necessarily in this order, ['g1', 'h2', 'h4', 'g5', 'e5', 'd4', 'd2', 'e1']
    """
    from_coordinate = square_to_coordinate(from_square)
    file_int = int(from_coordinate[0])
    rank_int = int(from_coordinate[1])
    knight_scope = []
    for rank_diff in (-2, 2):
        for file_diff in (-1, 1):
            file = file_int + file_diff
            rank = rank_int + rank_diff
            if 1 <= file <= 8 and 1 <= rank <= 8:
                knight_scope.append(coordinate_to_square(f'{file}{rank}'))
    for file_diff in (-2, 2):
        for rank_diff in (-1, 1):
            file = file_int + file_diff
            rank = rank_int + rank_diff
            if 1 <= file <= 8 and 1 <= rank <= 8:
                knight_scope.append(coordinate_to_square(f'{file}{rank}'))
    return knight_scope


def scan_qbr_scope(piece: str, from_square: str) -> Dict[str, List[str]]:
    if piece == 'R':
        return scan_rook_scope(from_square)
    elif piece == 'B':
        return scan_bishop_scope(from_square)
    elif piece == 'Q':
        return scan_queen_scope(from_square)
    else:
        raise ValueError(f'Invalid piece (\'{piece}\') for this function.')


def scan_kn_scope(piece: str, from_square: str) -> List[str]:
    if piece == 'K':
        return scan_king_scope(from_square)
    elif piece == 'N':
        return scan_knight_scope(from_square)
    else:
        raise ValueError(f'Invalid piece (\'{piece}\') for this function')


def extend_line(sq1: str, sq2: str) -> List[str]:
    """
    Assumes sq1 and sq2 are in line. Extends the line in the direction going from sq1 to sq2.
    e.g. sq1='e1', sq2='e4', returns ['e5', 'e6', 'e7', 'e8']
    :param sq1:
    :param sq2:
    :return:
    """
    coordinates1 = square_to_coordinate(sq1)
    coordinates2 = square_to_coordinate(sq2)
    file1 = int(coordinates1[0])
    file2 = int(coordinates2[0])
    file_direction = 0 if file1 == file2 else int((file2-file1)/abs(file2-file1))
    rank1 = int(coordinates1[1])
    rank2 = int(coordinates2[1])
    rank_direction = 0 if rank1 == rank2 else int((rank2-rank1)/abs(rank2-rank1))
    extended_squares = []
    for i in range(1, 7):
        file = file2 + (i * file_direction)
        rank = rank2 + (i * rank_direction)
        if 1 <= file <= 8 and 1 <= rank <= 8:
            extended_squares.append(coordinate_to_square(f'{file}{rank}'))
        else:
            break
    return extended_squares


PIECE_MOVE_TYPE_DICT = {'Q': ('f', 'r', 'd'), 'R': ('f', 'r'), 'B': ('d',), 'K': ('K',), 'N': ('N',)}
SQUARE_SCOPES_MAP = {}
for sq in ALL_SQUARES:
    SQUARE_SCOPES_MAP[sq] = scan_qbr_scope('Q', sq) | {'K': scan_kn_scope('K', sq)} | {'N': scan_kn_scope('N', sq)}

INT_SQUARES_MAP = {}
for origin_sq in SQUARE_SCOPES_MAP:
    scopes = SQUARE_SCOPES_MAP[origin_sq]
    for move_type in scopes:
        if move_type in ('f', 'r', 'd'):
            squares_in_line = scopes[move_type]
            for dest_sq in squares_in_line:
                INT_SQUARES_MAP[f'{origin_sq}{dest_sq}'] = {'line': move_type, 'int': get_intervening_squares(origin_sq, dest_sq, move_type)}

LINE_EXTEND_MAP = {}
for square_pair in INT_SQUARES_MAP:
    LINE_EXTEND_MAP[square_pair] = extend_line(square_pair[:2], square_pair[2:])
