from typing import List, Callable, Tuple, Dict
from random import uniform
import random
from classes.move import LegalMove
from classes.position import Position, opposite_color
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


def collapse_node(node: Node, aggregator: Callable[[List[float]], float]):
    leaves = search_downstream(node)
    values = [leave.get_value() for leave in leaves]
    value = aggregator(values)
    node.set_value(value)
    node.remove_all_children()


def select_top_n_moves(position: Position, evaluate: Callable[[Position], Dict[str, float]], n: int,
                       pick_n_threatening: int, fluctuation: float) -> Dict[str, List[Tuple[LegalMove, Position, float]]]:
    to_move = position.to_move()
    all_legal_moves = position.get_all_legal_moves_for_color(to_move)
    positions = [branch_from_position(position, move) for move in all_legal_moves]
    evaluation_scores = [evaluate(positions[i]) for i in range(len(positions))]
    all_mpe = [(all_legal_moves[i], positions[i], evaluation_scores[i]['eval']) for i in range(len(all_legal_moves))]
    evaluations = [(i, evaluation_scores[i]['eval'] + uniform(-fluctuation, fluctuation)) for i in range(len(positions))]
    threat_scores = [(i, evaluation_scores[i]['threat'] + evaluation_scores[i]['eval'] + uniform(-fluctuation, fluctuation)) for i in range(len(positions))]
    evaluations.sort(key=lambda x: x[1], reverse=True)
    threat_scores.sort(key=lambda x: x[1], reverse=True)
    returned_list = []
    for j in range(pick_n_threatening):
        if len(returned_list) >= n:
            break
        try:
            i = threat_scores[j][0]
            bare_threat_score = evaluation_scores[i]['threat']
            if bare_threat_score < 2:
                break
            move = all_legal_moves[i]
            position = positions[i]
            score = evaluations[i][1]
            returned_list.append((move, position, score))
        except IndexError:
            return {'top': returned_list, 'all': all_mpe}
    for j in range(len(evaluations)):
        if len(returned_list) >= n:
            break
        i = evaluations[j][0]
        move = all_legal_moves[i]
        if move.generate_uci() not in [tup[0].generate_uci() for tup in returned_list]:
            position = positions[i]
            score = evaluations[j][1]
            returned_list.append((move, position, score))
    return {'top': returned_list, 'all': all_mpe}


def make_4_ply_move_tree(initial_mpe_list: List[Tuple[LegalMove, Position, float]], evaluate: Callable[[Position], Dict[str, float]], n: int,
                         aggression: int, fluctuation: float = 0) -> Node:
    tree = Node('Current', 0)
    top_first_moves = initial_mpe_list
    for first_move_tup in top_first_moves:
        first_move = first_move_tup[0]
        position_after_first_move = first_move_tup[1]
        first_move_node = tree.add_child(first_move.generate_uci(), first_move_tup[2])
        top_first_replies = select_top_n_moves(position_after_first_move, evaluate, n, 1, fluctuation)['top']
        for first_reply_tup in top_first_replies:
            first_reply = first_reply_tup[0]
            position_after_first_reply = first_reply_tup[1]
            first_reply_node = first_move_node.add_child(f'{first_move_node.get_name()}-{first_reply.generate_uci()}',
                                                         first_reply_tup[2])
            top_second_moves = select_top_n_moves(position_after_first_reply, evaluate, n, aggression, fluctuation)['top']
            for second_move_tup in top_second_moves:
                second_move = second_move_tup[0]
                position_after_second_move = second_move_tup[1]
                second_move_node = first_reply_node.add_child(f'{first_move_node.get_name()}-{second_move.generate_uci()}',
                                                              second_move_tup[2])
                top_second_replies = select_top_n_moves(position_after_second_move, evaluate, n, 1, fluctuation)['top']
                for second_reply_tup in top_second_replies:
                    second_reply = second_reply_tup[0]
                    second_reply_node = second_move_node.add_child(f'{second_move_node.get_name()}-{second_reply.generate_uci()}',
                                                                   second_reply_tup[2])
    return tree


def collapse_at_level(tree: Node, level: int, aggregator: Callable[[List[float]], float]):
    all_leaves = search_downstream(tree)
    levels = [len(leave.get_name().split('-')) for leave in all_leaves]
    highest_level = max(levels)
    if highest_level == 1 or level > highest_level or level == 1:
        return
    collapsed_node_names = []
    for leave in all_leaves:
        if len(leave.get_name().split('-')) != level:
            continue
        if leave.get_name().rsplit('-', maxsplit=1)[0] not in collapsed_node_names:
            parent = leave.get_parent()
            collapse_node(parent, aggregator)
            collapsed_node_names.append(parent.get_name())


def choose_best_move(position: Position, evaluate: Callable[[Position], Dict[str, float]],
                     breadth: int,
                     aggression: int, fluctuation: float) -> str:
    """
    Returns a UCI notation e.g. 'd1h5'
    :param fluctuation:
    :param breadth:
    :param aggression:
    :param evaluate:
    :param position:
    :return:
    """
    initial_score = -evaluate(position)['eval']
    all_mpe_and_top = select_top_n_moves(position, evaluate, breadth, aggression, fluctuation)
    all_mpe = all_mpe_and_top['all']
    if len(all_mpe) == 1:
        return all_mpe[0][0].generate_uci()
    top_mpe = all_mpe_and_top['top']
    top_moves_uci = [mpe[0].generate_uci() for mpe in top_mpe]
    uci_mpe_dict = {}
    for mpe in all_mpe:
        uci_mpe_dict[mpe[0].generate_uci()] = mpe
    best_move, best_score = converge(aggression, breadth, evaluate, fluctuation, top_mpe)
    for uci in top_moves_uci:
        uci_mpe_dict.pop(uci)
    next_n_mpe = select_n_random_mpe(breadth, evaluate, initial_score, uci_mpe_dict)
    if not next_n_mpe:
        return best_move
    run2_best_move, run2_best_score = converge(aggression, breadth, evaluate, fluctuation, next_n_mpe)
    candidates = [(best_move, best_score), (run2_best_move, run2_best_score)]
    next_n_mpe = select_n_random_mpe(breadth, evaluate, initial_score, uci_mpe_dict)
    if next_n_mpe:
        run3_best_move, run3_best_score = converge(aggression, breadth, evaluate, fluctuation, next_n_mpe)
        candidates.append((run3_best_move, run3_best_score))
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def select_n_random_mpe(breadth, evaluate, initial_score, uci_mpe_dict):
    next_n_mpe = []
    while len(next_n_mpe) < breadth:
        if not uci_mpe_dict:
            break
        random_choice_uci = random.choice(list(uci_mpe_dict.keys()))
        mpe = uci_mpe_dict[random_choice_uci]
        score = mpe[2]
        if initial_score - score > 1.5:
            position = mpe[1]
            threat_score = evaluate(position)['threat']
            if threat_score < 7:
                uci_mpe_dict.pop(random_choice_uci)
                continue
        next_n_mpe.append(mpe)
        uci_mpe_dict.pop(random_choice_uci)
    return next_n_mpe


def converge(aggression, breadth, evaluation_func, fluctuation, mpe_list):
    tree = make_4_ply_move_tree(mpe_list, evaluation_func, breadth, aggression, fluctuation)
    collapse_at_level(tree, 4, lambda x: -max(x))
    collapse_at_level(tree, 3, max)
    collapse_at_level(tree, 2, lambda x: -max(x))
    candidate_moves = tree.get_children()
    best_move = candidate_moves[0].get_name()
    best_score = candidate_moves[0].get_value()
    for move in candidate_moves:
        move_score = move.get_value()
        if move_score > best_score:
            best_score = move_score
            best_move = move.get_name()
    return best_move, best_score

