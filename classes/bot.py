import json
from typing import Callable, Dict
from classes.position import Position
from simple_bot.move_search import choose_best_move, choose_best_move_recursive
from random import choice


class Bot:

    def __init__(self, evaluation_func: Callable[[Position], Dict[str, float]], breadth: int = 3,
                 aggression: int = 1, fluctuation: float = 0, assumed_opp_aggresion: int = 1,
                 ply_depth: int = 4, opening_book_path: str = None):
        self.evaluation_func = evaluation_func
        self.breadth = breadth
        self.aggression = aggression
        self.fluctuation = fluctuation
        self.assumed_opp_aggression = assumed_opp_aggresion
        self.ply_depth = ply_depth
        try:
            with open(opening_book_path, 'r') as readfile:
                opening_book = json.load(readfile)
        except Exception as e:
            print(f'Error getting opening book: {str(e)}. Bot will play without opening book.')
            opening_book = None
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
                return '0000'

    def make_move(self, position: Position) -> str:
        opening_book_move = self.look_in_opening_book(position)
        if opening_book_move != '0000':
            return opening_book_move
        else:
            return self.choose_move_recursive(position)
