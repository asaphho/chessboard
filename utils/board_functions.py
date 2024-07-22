from typing import Tuple, List

LETTER_TO_NUM = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8}
NUM_TO_LETTER = {}
for letter in LETTER_TO_NUM:
    NUM_TO_LETTER[LETTER_TO_NUM[letter]] = letter


def square_to_coordinate(square: str) -> str:
    file = square[0]
    file_num = LETTER_TO_NUM[file]
    rank = square[1]
    return f'{file_num}{rank}'


def coordinate_to_square(coordinate: str) -> str:
    file = NUM_TO_LETTER[coordinate[0]]
    return f'{file}{coordinate[1]}'


def check_squares_in_line(square1: str, square2: str) -> str:
    if square1 == square2:
        print(f"Cannot move from {square1} to {square2} as they are the same square.")
        raise ValueError
    file_diff, rank_diff = get_rank_and_file_diffs(square1, square2)
    if file_diff > 0 and rank_diff == 0:
        return 'rank'
    elif file_diff == 0 and rank_diff > 0:
        return 'file'
    elif file_diff == rank_diff:
        return 'diagonal'
    else:
        return 'Not in line'


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
    if line_type == 'file':
        if abs(rank1 - rank2) <= 1:
            return []
        squares = [f'{NUM_TO_LETTER[file1]}{rank}' for rank in make_range(rank1, rank2)]
    elif line_type == 'rank':
        if abs(file1 - file2) <= 1:
            return []
        squares = [f"{NUM_TO_LETTER[file]}{rank1}" for file in make_range(file1, file2)]
    elif line_type == 'diagonal':
        if abs(rank1 - rank2) <= 1:
            return []
        files = list(make_range(file1, file2))
        ranks = list(make_range(rank1, rank2))
        squares = [f"{NUM_TO_LETTER[files[i]]}{ranks[i]}" for i in range(len(files))]
    else:
        print(f'Unrecognized line type: {line_type}')
        raise ValueError
    return squares
