from typing import Callable, Dict
from classes.position import Position
from simple_bot.move_search import choose_best_move


class Bot:

    def __init__(self, evaluation_func: Callable[[Position], Dict[str, float]], breadth: int = 3,
                 aggression: int = 1, fluctuation: float = 0, assumed_opp_aggresion: int = 1,
                 ply_depth: int = 4):
        self.evaluation_func = evaluation_func
        self.breadth = breadth
        self.aggression = aggression
        self.fluctuation = fluctuation
        self.assumed_opp_aggression = assumed_opp_aggresion
        self.ply_depth = ply_depth

    def choose_move(self, position: Position) -> str:
        return choose_best_move(position=position, evaluate=self.evaluation_func, breadth=self.breadth,
                                aggression=self.aggression, fluctuation=self.fluctuation,
                                assumed_opp_aggression=self.assumed_opp_aggression, ply_depth=self.ply_depth)

