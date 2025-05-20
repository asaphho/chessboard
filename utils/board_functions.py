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
    Determines the color of a square on the chessboard.

    Args:
        square (str): The square in algebraic notation (e.g., 'e4').

    Returns:
        int: 0 for light square, 1 for dark square.
    """
    file = LETTER_TO_NUM[square[0]]
    rank = int(square[1])
    return int((file % 2) == (rank % 2))


def square_to_coordinate(square: str) -> str:
    """
        Converts a square (e.g., 'e4') to a numeric coordinate string (e.g., '54').

        Args:
            square (str): Square in algebraic notation.

        Returns:
            str: String representation of the numeric file and rank.
        """
    file = square[0]
    file_num = LETTER_TO_NUM[file]
    rank = square[1]
    return f'{file_num}{rank}'


def coordinate_to_square(coordinate: str) -> str:
    """
        Converts a numeric coordinate string (e.g., '54') back to a square (e.g., 'e4').

        Args:
            coordinate (str): A 2-digit string representing file and rank numbers.

        Returns:
            str: Square in algebraic notation.
        """
    file = NUM_TO_LETTER[int(coordinate[0])]
    return f'{file}{coordinate[1]}'


def check_squares_in_line(square1: str, square2: str) -> str:
    """
        Determines the type of line (rank, file, or diagonal) connecting two squares.

        Args:
            square1 (str): Starting square.
            square2 (str): Ending square.

        Returns:
            str: 'r' for same rank, 'f' for same file, 'd' for diagonal, 'N' if not aligned.

        Raises:
            ValueError: If the two squares are the same.
        """
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
    """
        Returns the absolute differences in file and rank between two squares.

        Args:
            square1 (str): First square.
            square2 (str): Second square.

        Returns:
            Tuple[int, int]: (file_diff, rank_diff)
        """
    coordinate1 = square_to_coordinate(square1)
    coordinate2 = square_to_coordinate(square2)
    file_diff = get_rank_or_file_diff(coordinate1, coordinate2, 'file')
    rank_diff = get_rank_or_file_diff(coordinate1, coordinate2, 'rank')
    return file_diff, rank_diff


def get_rank_or_file_diff(coordinate1: str, coordinate2: str, dimension: str) -> int:
    """
        Computes the difference in rank or file between two numeric coordinates.

        Args:
            coordinate1 (str): First coordinate (e.g., '54').
            coordinate2 (str): Second coordinate.
            dimension (str): 'file' or 'rank'.

        Returns:
            int: Absolute difference in the specified dimension.
        """
    return abs(int(coordinate1[0 if dimension == 'file' else 1]) - int(coordinate2[0 if dimension == 'file' else 1]))


def is_knight_move(square1: str, square2: str) -> bool:
    """
        Checks if the move between two squares is a legal knight move.

        Args:
            square1 (str): Starting square.
            square2 (str): Target square.

        Returns:
            bool: True if the move is a valid knight move, False otherwise.
        """
    diff_tuple = get_rank_and_file_diffs(square1, square2)
    return (diff_tuple == (2, 1)) or (diff_tuple == (1, 2))


def get_intervening_squares(square1: str, square2: str, line_type: str) -> List[str]:
    """
        Returns the list of squares strictly between two aligned squares.

        Args:
            square1 (str): Starting square.
            square2 (str): Ending square.
            line_type (str): 'r' for rank, 'f' for file, 'd' for diagonal.

        Returns:
            List[str]: List of intervening square strings.

        Raises:
            ValueError: If the line type is not recognized.
        """
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
    Returns all squares a rook can move to from a given square on an empty board.

    Args:
        from_square (str): The starting square.

    Returns:
        Dict[str, List[str]]: {'f': forward/backward moves, 'r': lateral moves}
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
    Returns all squares a bishop can reach from a given square on an empty board.

    Args:
        from_square (str): The starting square.

    Returns:
        Dict[str, List[str]]: {'d': list of diagonally-linked squares}
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
    Returns all squares a queen can move to from a given square on an empty board.

    Args:
        from_square (str): The starting square.

    Returns:
        Dict[str, List[str]]: Combined rook and bishop move scopes.
    """
    return scan_rook_scope(from_square) | scan_bishop_scope(from_square)


def scan_king_scope(from_square: str) -> List[str]:
    """
    Returns all adjacent squares a king can move to from a given square.

    Args:
        from_square (str): The starting square.

    Returns:
        List[str]: Squares surrounding the given square (up to 8).
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
    Returns all squares a knight can reach from a given square.

    Args:
        from_square (str): The starting square.

    Returns:
        List[str]: List of squares reachable by the knight from the starting square.
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
    """
        Returns the movement scope of a queen, bishop, or rook from a square.

        Args:
            piece (str): 'Q', 'B', or 'R'.
            from_square (str): The starting square.

        Returns:
            Dict[str, List[str]]: Movement map for the given piece.

        Raises:
            ValueError: If the piece is not one of 'Q', 'B', or 'R'.
        """
    if piece == 'R':
        return scan_rook_scope(from_square)
    elif piece == 'B':
        return scan_bishop_scope(from_square)
    elif piece == 'Q':
        return scan_queen_scope(from_square)
    else:
        raise ValueError(f'Invalid piece (\'{piece}\') for this function.')


def scan_kn_scope(piece: str, from_square: str) -> List[str]:
    """
        Returns the movement scope of a king or knight from a square.

        Args:
            piece (str): 'K' or 'N'.
            from_square (str): The starting square.

        Returns:
            List[str]: List of squares the piece can move to.

        Raises:
            ValueError: If the piece is not 'K' or 'N'.
        """
    if piece == 'K':
        return scan_king_scope(from_square)
    elif piece == 'N':
        return scan_knight_scope(from_square)
    else:
        raise ValueError(f'Invalid piece (\'{piece}\') for this function')


def extend_line(sq1: str, sq2: str) -> List[str]:
    """
    Extends the line formed by two squares outward in the same direction.

    Assumes the squares are aligned in a valid direction (rank, file, or diagonal).

    Args:
        sq1 (str): Starting square.
        sq2 (str): Next square in direction.

    Returns:
        List[str]: List of squares extending beyond sq2 in the same direction.
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
