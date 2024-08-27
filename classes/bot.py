import json
from typing import Callable, Dict, Any
from classes.position import Position
from simple_bot.move_search import choose_best_move, choose_best_move_recursive
from random import choice


class Bot:

    def __init__(self, evaluation_func: Callable[[Position], Dict[str, float]], breadth: int = 3,
                 aggression: int = 1, fluctuation: float = 0, assumed_opp_aggression: int = 1,
                 ply_depth: int = 4, opening_book_path: str = None):
        self.evaluation_func = evaluation_func
        self.breadth = breadth
        self.aggression = aggression
        self.fluctuation = fluctuation
        self.assumed_opp_aggression = assumed_opp_aggression
        self.ply_depth = ply_depth
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

    def choose_move(self, position: Position) -> str:
        return choose_best_move(position=position, evaluate=self.evaluation_func, breadth=self.breadth,
                                aggression=self.aggression, fluctuation=self.fluctuation,
                                assumed_opp_aggression=self.assumed_opp_aggression, ply_depth=self.ply_depth)

    def choose_move_recursive(self, position: Position) -> str:
        return choose_best_move_recursive(position=position, evaluation_func=self.evaluation_func, breadth=self.breadth,
                                          aggression=self.aggression, fluctuation=self.fluctuation,
                                          assumed_opp_aggression=self.assumed_opp_aggression,
                                          ply_depth=self.ply_depth)[0]

    def look_in_opening_book(self, position: Position) -> str:
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
        opening_book_move = self.look_in_opening_book(position)
        if opening_book_move != '0000':
            return opening_book_move
        else:
            return self.choose_move_recursive(position)

    def remove_bad_uci(self, fen: str, bad_uci: str):
        uci_list = self.opening_book[fen]
        for i in range(len(uci_list)):
            if uci_list[i] == bad_uci:
                self.opening_book[fen].pop(i)
                if len(self.opening_book[fen]) == 0:
                    self.opening_book.pop(fen)
                break



