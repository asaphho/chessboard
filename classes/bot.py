from typing import Callable, Dict
from classes.position import Position
from simple_bot.move_search import choose_best_move


class Bot:

    def __init__(self, evaluation_func: Callable[[Position], Dict[str, float]]):
        self.evaluation_func = evaluation_func

    def choose_move(self, position: Position) -> str:
        return choose_best_move(position, self.evaluation_func)

