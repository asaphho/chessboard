from typing import Callable, Dict
from classes.position import Position
from simple_bot.move_search import choose_best_move


class Bot:

    def __init__(self, evaluation_func: Callable[[Position], Dict[str, float]], breadth: int,
                 pick_n_threatening: int, fluctuation: float = 0):
        self.evaluation_func = evaluation_func
        self.breadth = breadth
        self.aggression = pick_n_threatening
        self.fluctuation = fluctuation

    def choose_move(self, position: Position) -> str:
        return choose_best_move(position, self.evaluation_func, self.breadth, self.aggression, self.fluctuation)

