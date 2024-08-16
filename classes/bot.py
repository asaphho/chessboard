from typing import Callable, Dict
from classes.position import Position
from simple_bot.move_search import choose_best_move


class Bot:

    def __init__(self, evaluation_func: Callable[[Position], Dict[str, float]], breadth: int,
                 pick_n_threatening: int, fluctuation: float = 0, assumed_opp_aggresion: int = 1):
        self.evaluation_func = evaluation_func
        self.breadth = breadth
        self.aggression = pick_n_threatening
        self.fluctuation = fluctuation
        self.assumed_opp_aggression = assumed_opp_aggresion

    def choose_move(self, position: Position) -> str:
        return choose_best_move(position=position, evaluate=self.evaluation_func, breadth=self.breadth,
                                aggression=self.aggression, fluctuation=self.fluctuation,
                                assumed_opp_aggression=self.assumed_opp_aggression)

