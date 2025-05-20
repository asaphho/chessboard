from typing import List, Callable, Tuple, Dict
from random import uniform
from classes.move import LegalMove
from classes.position import Position
from simple_bot.utils import branch_from_position


class Node:

    def __init__(self, name: str, value, parent=None):
        self.parent = parent
        self.children = []
        self.name = name
        self.value = value

    def get_parent(self):
        return self.parent

    def add_child(self, name, value):
        child = Node(name, value, self)
        self.children.append(child)
        return child

    def remove_all_children(self):
        self.children = []

    def get_name(self) -> str:
        return self.name

    def get_children(self) -> list:
        return self.children

    def get_siblings(self) -> List:
        return [node for node in self.get_parent().get_children() if node.get_name() != self.get_name()]

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    def is_leaf(self) -> bool:
        return self.get_children() == []


def search_downstream(node: Node) -> List[Node]:
    if node.is_leaf():
        return [node]
    else:
        children = node.get_children()
        leaves = []
        for child in children:
            leaves.extend(search_downstream(child))
        return leaves


def search_upstream(node: Node) -> Node:
    if node.get_parent() is None:
        return node
    else:
        return search_upstream(node.get_parent())


def select_top_n_moves(position: Position, evaluate: Callable[[Position, Dict[int, float]], Dict[str, float]], n: int,
                       pick_n_threatening: int, fluctuation: float = 0, params: Dict[int, float] = None) -> Dict[
    str, List[Tuple[LegalMove, Position, float]]]:
    """
        Evaluates all legal moves and selects the top N based on evaluation scores and threat potential.

        Adds randomness (`fluctuation`) to scores for diversity. Also filters for aggressive or high-threat moves
        using the `pick_n_threatening` parameter.

        Args:
            position (Position): Current game position.
            evaluate (Callable): A function that returns an evaluation dictionary for a position.
            n (int): Max number of top moves to return.
            pick_n_threatening (int): Number of high-threat moves to prioritize.
            fluctuation (float): Random fluctuation added to evals (for unpredictability).
            params (Dict[int, float], optional): Extra parameters to pass to the evaluation function.

        Returns:
            Dict[str, List[Tuple[LegalMove, Position, float]]]: A dictionary with:
                - 'top': Top `n` moves after filtering.
                - 'all': All evaluated moves with noisy scores.
        """
    to_move = position.to_move()
    initial_score = -evaluate(position, params)['eval']
    all_legal_moves = position.get_all_legal_moves_for_color(to_move)
    positions = [branch_from_position(position, move) for move in all_legal_moves]
    evaluation_scores = [evaluate(posn, params) for posn in positions]
    uci_bare_evaluation_dict: Dict[str, Dict[str, float]] = {}
    for i in range(len(all_legal_moves)):
        uci_bare_evaluation_dict[all_legal_moves[i].generate_uci()] = evaluation_scores[i]
    all_mpe = [(all_legal_moves[i], positions[i], evaluation_scores[i]['eval'] + uniform(-fluctuation, fluctuation)) for
               i in range(len(all_legal_moves))]
    if len(all_mpe) <= n:
        return {'top': all_mpe, 'all': all_mpe}
    all_mpe_threat_scores = [(all_legal_moves[i], positions[i], evaluation_scores[i]['threat']) for i in
                             range(len(all_legal_moves))]
    all_mpe.sort(key=lambda x: x[2], reverse=True)
    all_mpe_threat_scores.sort(key=lambda x: x[2], reverse=True)
    returned_list = []
    for j in range(pick_n_threatening):
        if len(returned_list) >= n:
            break
        try:
            move_uci = all_mpe_threat_scores[j][0].generate_uci()
            eval_score = uci_bare_evaluation_dict[move_uci]['eval']
            bare_threat_score = all_mpe_threat_scores[j][2]
            if bare_threat_score < 2:
                break
            if initial_score - eval_score > 1.5 and bare_threat_score < 7:
                continue
            move = all_mpe_threat_scores[j][0]
            position = all_mpe_threat_scores[j][1]
            returned_list.append((move, position, eval_score))
            uci_bare_evaluation_dict.pop(move_uci)
        except IndexError:
            return {'top': returned_list, 'all': all_mpe}
    for j in range(n):
        if len(returned_list) >= n:
            break
        try:
            move = all_mpe[j][0]
            if move.generate_uci() in uci_bare_evaluation_dict:
                position = all_mpe[j][1]
                score = all_mpe[j][2]
                returned_list.append((move, position, score))
        except IndexError:
            return {'top': returned_list, 'all': all_mpe}
    return {'top': returned_list, 'all': all_mpe}


def choose_best_move_recursive(position: Position, evaluation_func: Callable[[Position, Dict[int, float]], Dict[str, float]],
                               breadth: int = 3, aggression: int = 1, fluctuation: float = 0,
                               assumed_opp_aggression: int = 1, ply_depth: int = 4, params: Dict[int, float] = None) -> Tuple[str, float]:
    """
    Recursively searches the move tree to select the best move using a shallow minimax-like strategy.

    Alternates between maximizing and minimizing depending on the side to move, with parameters for
    search breadth, depth, aggressiveness, and noise.

    Args:
        position (Position): Current board state.
        evaluation_func (Callable): Function to evaluate positions.
        breadth (int): Number of top candidate moves to consider at each ply.
        aggression (int): Number of top aggressive (threat-based) moves to include.
        fluctuation (float): Random noise added to evaluation to simulate unpredictability.
        assumed_opp_aggression (int): Aggression level to assume for the opponent.
        ply_depth (int): Total depth to search (1 = static eval).
        params (Dict[int, float], optional): Extra arguments for the evaluation function.

    Returns:
        Tuple[str, float]: UCI string of the chosen move, and its evaluated score.
    """
    all_mpe = select_top_n_moves(position=position, evaluate=evaluation_func, n=breadth, pick_n_threatening=aggression,
                                 fluctuation=fluctuation, params=params)
    if len(all_mpe['all']) == 0:
        if position.is_under_check(position.to_move()):
            return '0000', -9999
        else:
            return '0000', 0

    if len(all_mpe['all']) == 1:
        return all_mpe['all'][0][0].generate_uci(), all_mpe['all'][0][2]

    if ply_depth == 1:
        return all_mpe['all'][0][0].generate_uci(), all_mpe['all'][0][2]
    else:
        candidate_mpes = all_mpe['top']
        candidate_moves_uci = [mpe[0].generate_uci() for mpe in candidate_mpes]
        uci_position_dict: Dict[str, Position] = {}
        for mpe in candidate_mpes:
            uci_position_dict[mpe[0].generate_uci()] = mpe[1]
        uci_score_dict: Dict[str, float] = {}
        for uci in candidate_moves_uci:
            uci_score_dict[uci] = -1 * \
                                  choose_best_move_recursive(position=uci_position_dict[uci],
                                                             evaluation_func=evaluation_func,
                                                             breadth=breadth, aggression=assumed_opp_aggression,
                                                             fluctuation=fluctuation, assumed_opp_aggression=aggression,
                                                             ply_depth=ply_depth - 1, params=params)[1]
        best_move = candidate_moves_uci[0]
        best_score = uci_score_dict[best_move]
        for uci in uci_score_dict:
            score = uci_score_dict[uci]
            if score > best_score:
                best_score = score
                best_move = uci
        return best_move, best_score
