def find_destination_square(move_str: str) -> str:
    rank = 0
    file = 'z'
    for i in range(len(move_str) - 1, -1, -1):
        if move_str[i].isnumeric():
            rank = int(move_str[i])
            if i == 0:
                print('Cannot interpret this move!')
                raise ValueError
            file = move_str[i-1].lower()
            if file.isnumeric():
                print('Cannot interpret this move!')
                raise ValueError
            break
    if rank == 0 or file == 'z':
        print('Cannot interpret this move!')
        raise ValueError
    if rank > 8 or rank < 1:
        print(f'Square {file}{rank} does not exist.')
        raise ValueError
    if file not in 'abcdefgh':
        print(f'Square {file}{rank} does not exist.')
        raise ValueError
    return f'{file}{rank}'


def find_piece_moved(move_str: str) -> str:
    piece_symbols = {'K': 'king', 'Q': 'queen', 'R': 'rook', 'B': 'bishop', 'N': 'knight'}
    first_char = move_str[0]
    if first_char in piece_symbols:
        return piece_symbols[first_char]
    elif first_char.lower() in 'abcdefgh':
        return 'pawn'
    else:
        print('Could not figure out which piece is to be moved. Piece symbols, except for pawns, must be given in uppercase.')
        raise ValueError


