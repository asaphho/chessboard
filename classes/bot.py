import json
from typing import Callable, Dict
from classes.position import Position
from simple_bot.move_search import choose_best_move_recursive
from random import choice


class Bot:
    """
        A chess-playing engine that chooses moves based on evaluation heuristics, recursive minimax-style search,
        and optionally an opening book.

        The bot supports:
            - Recursive evaluation-based move search with adjustable depth and breadth.
            - Randomized selection within top moves (via evaluation noise).
            - Threat-based prioritization and opponent modeling.
            - Use of an opening book for fast early-game decisions.

        Attributes:
            evaluation_func (Callable): A function that evaluates a `Position` and returns a dict with 'eval' and 'threat'.
            breadth (int): Max number of top candidate moves to consider per position.
            aggression (int): How many of the top threatening moves to include in each candidate list.
            fluctuation (float): Amount of random noise to add to evaluation scores (adds unpredictability).
            assumed_opp_aggression (int): Aggression level to assume for the opponent when simulating replies.
            ply_depth (int): Total search depth (in plies).
            params (Dict[int, float]): Optional evaluation parameters.
            opening_book (Dict[str, List[str]]): A FEN-to-UCIs dictionary used for opening play.
        """

    def __init__(self, evaluation_func: Callable[[Position, Dict[int, float]], Dict[str, float]], breadth: int = 3,
                 aggression: int = 1, fluctuation: float = 0, assumed_opp_aggression: int = 1,
                 ply_depth: int = 4, opening_book_path: str = None, bot_params: Dict[int, float] = None):
        """
            Initializes the bot with evaluation and search settings, and optionally loads an opening book.

            Args:
                evaluation_func (Callable): Function that evaluates a Position and returns a score dictionary.
                breadth (int): Number of best moves to consider at each node (width of search tree).
                aggression (int): Number of threat-heavy moves to include in candidate set.
                fluctuation (float): Amount of random evaluation noise to inject into decisions.
                assumed_opp_aggression (int): Opponent aggression level to simulate during evaluation.
                ply_depth (int): Maximum search depth in half-moves.
                opening_book_path (str, optional): File path to a JSON opening book. Default is None.
                bot_params (Dict[int, float], optional): Dictionary of parameters passed into the evaluation function.
            """
        self.evaluation_func = evaluation_func
        self.breadth = breadth
        self.aggression = aggression
        self.fluctuation = fluctuation
        self.assumed_opp_aggression = assumed_opp_aggression
        self.ply_depth = ply_depth
        self.params = bot_params
        if opening_book_path:
            try:
                with open(opening_book_path, 'r') as readfile:
                    opening_book = json.load(readfile)
            except Exception as e:
                print(f'Error getting opening book: {str(e)}. Bot will play without opening book.')
                opening_book = None
        else:
            opening_book = None
        if opening_book:
            for fen in list(opening_book.keys()):
                if type(fen) != str:
                    opening_book.pop(fen)
            for fen in list(opening_book.keys()):
                if type(opening_book[fen]) != list:
                    opening_book.pop(fen)
            for fen in list(opening_book.keys()):
                uci_list = opening_book[fen]
                indices_to_remove = []
                for i in range(len(uci_list)):
                    if type(uci_list[i]) != str:
                        indices_to_remove.append(i)
                if indices_to_remove:
                    indices_to_remove.sort(reverse=True)
                    for i in indices_to_remove:
                        opening_book[fen].pop(i)
            for fen in list(opening_book.keys()):
                if len(opening_book[fen]) == 0:
                    opening_book.pop(fen)
        self.opening_book = opening_book

    def choose_move_recursive(self, position: Position) -> str:
        """
            Chooses a move from the given position using recursive evaluation search.

            Returns:
                str: The UCI string of the best move found (e.g. 'e2e4').
            """
        return choose_best_move_recursive(position=position, evaluation_func=self.evaluation_func, breadth=self.breadth,
                                          aggression=self.aggression, fluctuation=self.fluctuation,
                                          assumed_opp_aggression=self.assumed_opp_aggression,
                                          ply_depth=self.ply_depth, params=self.params)[0]

    def look_in_opening_book(self, position: Position) -> str:
        """
            Checks the bot’s opening book to find a valid move for the current position.

            Returns:
                str: A UCI move string from the opening book if found, or '0000' if not found.
            """
        if not self.opening_book:
            return '0000'
        current_fen = position.generate_fen().rsplit(' ', maxsplit=2)[0]
        if current_fen not in self.opening_book:
            return '0000'
        else:
            try:
                return choice(self.opening_book[current_fen])
            except Exception:
                self.opening_book.pop(current_fen)
                return '0000'

    def make_move(self, position: Position) -> str:
        """
            Determines a move to play from the given position. If the position is in the opening book, uses that.
            Otherwise, performs a recursive evaluation-based search.

            Returns:
                str: The UCI move string chosen by the bot.
            """
        opening_book_move = self.look_in_opening_book(position)
        if opening_book_move != '0000':
            return opening_book_move
        else:
            return self.choose_move_recursive(position)

    def remove_bad_uci(self, fen: str, bad_uci: str):
        """
            Removes a bad or invalid UCI move string from the opening book at a specific FEN key.

            Args:
                fen (str): FEN string representing the board state.
                bad_uci (str): The UCI move to be removed.
            """
        uci_list = self.opening_book[fen]
        for i in range(len(uci_list)):
            if uci_list[i] == bad_uci:
                self.opening_book[fen].pop(i)
                if len(self.opening_book[fen]) == 0:
                    self.opening_book.pop(fen)
                break



