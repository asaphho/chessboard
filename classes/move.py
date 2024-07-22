class LegalMove:

    def __init__(self, color: str, piece: str, origin_square: str, destination_square: str, is_capture: bool = False,
                 is_en_passant_capture: bool = False, promotion_piece: str = None, castling: str = None):
        self.color = color.lower()
        self.piece_moved = piece.lower()
        self.origin_square = origin_square
        self.destination_square = destination_square
        self.capture = is_capture
        self.en_passant_capture = is_en_passant_capture
        self.promotion_piece = promotion_piece
        self.castling = castling

    def get_color(self) -> str:
        return self.color

    def is_king_move(self) -> bool:
        return self.piece_moved == 'king'

    def is_pawn_move(self) -> bool:
        return self.piece_moved == 'pawn'

    def is_capture(self) -> bool:
        return self.capture

    def is_en_passant_capture(self) -> bool:
        return self.en_passant_capture

    def moved_queen_rook_from_home_square(self) -> bool:
        if self.color == 'white':
            return self.piece_moved == 'rook' and self.origin_square == 'a1'
        else:
            return self.piece_moved == 'rook' and self.origin_square == 'a8'

    def moved_king_rook_from_home_square(self) -> bool:
        if self.color == 'white':
            return self.piece_moved == 'rook' and self.origin_square == 'h1'
        else:
            return self.piece_moved == 'rook' and self.origin_square == 'h8'

    def moved_to_opponents_queen_rook_home_square(self) -> bool:
        if self.color == 'white':
            return self.destination_square == 'a8'
        else:
            return self.destination_square == 'a1'

    def moved_to_opponents_king_rook_home_square(self) -> bool:
        if self.color == 'white':
            return self.destination_square == 'h8'
        else:
            return self.destination_square == 'h1'

    def is_pawn_2_square_move(self) -> bool:
        if self.piece_moved == 'pawn':
            if self.color == 'white':
                if self.origin_square[1] == '2':
                    if self.destination_square[1] == '4':
                        return True
            else:
                if self.origin_square[1] == '7':
                    if self.destination_square[1] == '5':
                        return True
        return False

    def pawn_promotion_required(self) -> bool:
        if self.piece_moved == 'pawn':
            if self.color == 'white':
                if self.destination_square[1] == '8':
                    return True
            else:
                if self.destination_square[1] == '1':
                    return True
        return False


class VirtualMove:

    def __init__(self, from_square: str, to_square: str):
        self.origin_square = from_square
        self.destination_square = to_square

    def get_origin_square(self) -> str:
        return self.origin_square

    def get_destination_square(self) -> str:
        return self.destination_square
