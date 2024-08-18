from typing import List, Callable, Tuple, Dict, Union, Iterable
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
                       pick_n_threatening: int, fluctuation: float = 0) -> Dict[
    str, List[Tuple[LegalMove, Position, float]]]:
    to_move = position.to_move()
    initial_score = -evaluate(position)['eval']
    all_legal_moves = position.get_all_legal_moves_for_color(to_move)
    positions = [branch_from_position(position, move) for move in all_legal_moves]
    evaluation_scores = [evaluate(posn) for posn in positions]
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


def make_4_ply_move_tree(initial_mpe_list: List[Tuple[LegalMove, Position, float]],
                         evaluate: Callable[[Position], Dict[str, float]], n: int,
                         aggression: int, fluctuation: float = 0, assumed_opp_aggression: int = 1) -> Node:
    tree = Node('Current', 0)
    top_first_moves = initial_mpe_list
    for first_move_tup in top_first_moves:
        first_move = first_move_tup[0]
        position_after_first_move = first_move_tup[1]
        first_move_node = tree.add_child(first_move.generate_uci(), first_move_tup[2])
        top_first_replies = \
            select_top_n_moves(position_after_first_move, evaluate, n, assumed_opp_aggression, fluctuation)['top']
        for first_reply_tup in top_first_replies:
            first_reply = first_reply_tup[0]
            position_after_first_reply = first_reply_tup[1]
            first_reply_node = first_move_node.add_child(f'{first_move_node.get_name()}-{first_reply.generate_uci()}',
                                                         first_reply_tup[2])
            top_second_moves = select_top_n_moves(position_after_first_reply, evaluate, n, aggression, fluctuation)[
                'top']
            for second_move_tup in top_second_moves:
                second_move = second_move_tup[0]
                position_after_second_move = second_move_tup[1]
                second_move_node = first_reply_node.add_child(
                    f'{first_move_node.get_name()}-{second_move.generate_uci()}',
                    second_move_tup[2])
                top_second_replies = \
                    select_top_n_moves(position_after_second_move, evaluate, n, assumed_opp_aggression, fluctuation)[
                        'top']
                for second_reply_tup in top_second_replies:
                    second_reply = second_reply_tup[0]
                    second_reply_node = second_move_node.add_child(
                        f'{second_move_node.get_name()}-{second_reply.generate_uci()}',
                        second_reply_tup[2])
    return tree


def make_move_tree(initial_mpe_list: List[Tuple[LegalMove, Position, float]],
                   evaluate: Callable[[Position], Dict[str, float]], breadth: int = 3, aggression: int = 1,
                   fluctuation: float = 0, assumed_opp_aggression: int = 1, ply_depth: int = 4) -> Node:
    tree = Node('Current', 0)

    def create_new_node_name(node: Node, move: LegalMove) -> str:
        if node.get_name() == 'Current':
            return move.generate_uci()
        else:
            return f'{node.get_name()}-{move.generate_uci()}'

    current_depth = 1
    while current_depth <= ply_depth:
        agg = aggression if (current_depth % 2) else assumed_opp_aggression
        if current_depth == 1:
            for mpe in initial_mpe_list:
                tree.add_child(create_new_node_name(tree, mpe[0]), {'P': mpe[1], 'S': mpe[2]})
        else:
            current_leaves = search_downstream(tree)
            for leaf in current_leaves:
                position: Position = leaf.get_value()['P']
                top_n_moves = select_top_n_moves(position, evaluate, n=breadth, pick_n_threatening=agg,
                                                 fluctuation=fluctuation)['top']
                for mpe in top_n_moves:
                    leaf.add_child(create_new_node_name(leaf, mpe[0]), {'P': mpe[1], 'S': mpe[2]})
        current_depth += 1
    return tree


def aggregator(leaf_vals: Iterable) -> float:
    def e(val):
        return val if (type(val) == float or type(val) == int) else val['S']

    return max([e(leaf_val) for leaf_val in leaf_vals])


def collapse_at_level(tree: Node, level: int, aggregator: Callable[[List[Union[Position, float]]], float]):
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
                     breadth: int = 3, aggression: int = 1, fluctuation: float = 0, assumed_opp_aggression: int = 1,
                     ply_depth: int = 4) -> str:
    """
    Returns a UCI notation e.g. 'd1h5'
    :param ply_depth:
    :param assumed_opp_aggression:
    :param fluctuation:
    :param breadth:
    :param aggression:
    :param evaluate:
    :param position:
    :return:
    """
    initial_score = -evaluate(position)['eval']
    all_mpe_and_top = select_top_n_moves(position=position, evaluate=evaluate, n=breadth,
                                         pick_n_threatening=aggression, fluctuation=fluctuation)
    all_mpe = all_mpe_and_top['all']
    if len(all_mpe) == 1:
        return all_mpe[0][0].generate_uci()
    top_mpe = all_mpe_and_top['top']
    top_moves_uci = [mpe[0].generate_uci() for mpe in top_mpe]
    uci_mpe_dict = {}
    for mpe in all_mpe:
        uci_mpe_dict[mpe[0].generate_uci()] = mpe
    best_move, best_score = converge(mpe_list=top_mpe, evaluation_func=evaluate, breadth=breadth, aggression=aggression,
                                     fluctuation=fluctuation, assumed_opp_aggression=assumed_opp_aggression,
                                     tree_ply_depth=ply_depth, aggregator=aggregator)
    for uci in top_moves_uci:
        uci_mpe_dict.pop(uci)
    next_n_mpe = select_n_random_mpe(breadth=breadth, evaluate=evaluate, initial_score=initial_score,
                                     uci_mpe_dict=uci_mpe_dict)
    if not next_n_mpe:
        return best_move
    run2_best_move, run2_best_score = converge(mpe_list=next_n_mpe, evaluation_func=evaluate, breadth=breadth,
                                               aggression=aggression, fluctuation=fluctuation, aggregator=aggregator,
                                               assumed_opp_aggression=assumed_opp_aggression, tree_ply_depth=ply_depth)
    candidates = [(best_move, best_score), (run2_best_move, run2_best_score)]
    # next_n_mpe = select_n_random_mpe(breadth, evaluate, initial_score, uci_mpe_dict)
    # if next_n_mpe:
    #     run3_best_move, run3_best_score = converge(aggression, breadth, evaluate, fluctuation, next_n_mpe)
    #     candidates.append((run3_best_move, run3_best_score))
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def select_n_random_mpe(breadth: int, evaluate: Callable[[Position], Dict[str, float]], initial_score: float,
                        uci_mpe_dict: Dict[str, Tuple[LegalMove, Position, float]]) -> List[
    Tuple[LegalMove, Position, float]]:
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


def converge(mpe_list, evaluation_func, breadth: int = 3, aggression: int = 1, fluctuation: float = 0,
             assumed_opp_aggression: int = 0, tree_ply_depth: int = 4, aggregator: Callable[[Iterable], float] = max) -> \
        Tuple[str, float]:
    tree = make_move_tree(initial_mpe_list=mpe_list, evaluate=evaluation_func, breadth=breadth, aggression=aggression,
                          fluctuation=fluctuation, assumed_opp_aggression=assumed_opp_aggression,
                          ply_depth=tree_ply_depth)
    for i in range(tree_ply_depth, 1, -1):
        if i % 2:
            collapse_at_level(tree=tree, level=i, aggregator=aggregator)
        else:
            collapse_at_level(tree=tree, level=i, aggregator=lambda x: -aggregator(x))

    candidate_moves = tree.get_children()
    best_move = candidate_moves[0].get_name()
    best_score = candidate_moves[0].get_value()
    for move in candidate_moves:
        move_score = move.get_value()
        if move_score > best_score:
            best_score = move_score
            best_move = move.get_name()
    return best_move, best_score


def choose_best_move_recursive(position: Position, evaluation_func: Callable[[Position], Dict[str, float]],
                               breadth: int = 3, aggression: int = 1, fluctuation: float = 0,
                               assumed_opp_aggression: int = 1, ply_depth: int = 4) -> Tuple[str, float]:
    """

    :param position:
    :param evaluation_func:
    :param breadth:
    :param aggression:
    :param fluctuation:
    :param assumed_opp_aggression:
    :param ply_depth:
    :return:
    """
    all_mpe = select_top_n_moves(position=position, evaluate=evaluation_func, n=breadth, pick_n_threatening=aggression,
                                 fluctuation=fluctuation)
    if len(all_mpe['all']) == 0:
        if position.is_under_check(position.to_move()):
            return '0000', -9999
        else:
            return '0000', 0
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
                                                             ply_depth=ply_depth - 1)[1]
        best_move = candidate_moves_uci[0]
        best_score = uci_score_dict[best_move]
        for uci in uci_score_dict:
            score = uci_score_dict[uci]
            if score > best_score:
                best_score = score
                best_move = uci
        return best_move, best_score
