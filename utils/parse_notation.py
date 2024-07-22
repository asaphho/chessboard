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


