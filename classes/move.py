class LegalMove:

    def __init__(self, color: str, piece_type: str, origin_square: str, destination_square: str, is_capture: bool = False,
                 is_en_passant_capture: bool = False, promotion_piece: str = None, castling: str = None):
        self.color = color.lower()
        self.piece_moved = piece_type.lower()
        self.origin_square = origin_square
        self.destination_square = destination_square
        self.capture = is_capture
        self.en_passant_capture = is_en_passant_capture
        self.promotion_piece = promotion_piece if promotion_piece is not None else 'None'
        self.castling = castling if castling is not None else 'None'

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

    def __init__(self, color: str, piece_type: str, from_square: str, to_square: str):
        self.origin_square = from_square
        self.destination_square = to_square
        self.color = color
        self.piece_type = piece_type

    def get_origin_square(self) -> str:
        return self.origin_square

    def get_destination_square(self) -> str:
        return self.destination_square

    def get_color(self) -> str:
        return self.color

    def get_piece_type(self) -> str:
        return self.piece_type

    def make_legal_move(self, is_capture: bool, is_en_passant_capture: bool, castling: str = None,
                        promotion_piece: str = None) -> LegalMove:
        return LegalMove(color=self.get_color(),
                         piece_type=self.get_piece_type(),
                         origin_square=self.get_origin_square(),
                         destination_square=self.get_destination_square(),
                         is_capture=is_capture,
                         is_en_passant_capture=is_en_passant_capture,
                         castling=castling,
                         promotion_piece=promotion_piece)
