from classes.color_position import ColorPosition, generate_starting_position_for_color

white_king_and_rooks = {'king': ['e1'], 'rook': ['a1', 'h1']}
p1 = ColorPosition(color='white', all_piece_squares=white_king_and_rooks.copy(), short_castle=True, long_castle=True)

# test get_king_square
assert p1.get_king_square() == 'e1'

# test move_piece
p1.move_piece('king', 'e1', 'd1')
assert p1.all_piece_squares['king'] == ['d1']
p1.move_piece('king', 'd1', 'f3')
assert p1.all_piece_squares['king'] == ['f3']
assert p1.get_king_square() == 'f3'

# test plant_piece
p1.plant_piece('bishop', 'c4')
assert p1.all_piece_squares['bishop'] == ['c4']

# test remove_piece
p1.remove_piece_on_square('a1')
assert p1.all_piece_squares['rook'] == ['h1']
p1.remove_piece_on_square('h1')
assert 'rook' not in p1.all_piece_squares

# test promote_pawn
p1.plant_piece('pawn', 'c8')
assert p1.all_piece_squares['pawn'] == ['c8']
p1.promote_pawn('c8', 'knight')
assert 'pawn' not in p1.all_piece_squares
assert p1.all_piece_squares['knight'] == ['c8']

# test get_occupied_squares
occupied_squares = p1.get_occupied_squares()
assert len(occupied_squares) == 3
assert set(occupied_squares) == {'f3', 'c4', 'c8'}

# test get_square_piece_symbol_dict
assert p1.get_square_piece_symbol_dict() == {'f3': 'K', 'c4': 'B', 'c8': 'N'}
