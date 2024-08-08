from typing import List, Callable

from classes.position import Position, opposite_color
from simple_bot.parameters import CHECKMATE_SCORE
from simple_bot.evaluation import evaluate
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


def make_4_ply_move_tree(position: Position) -> Node:
    side_to_move = position.to_move()
    tree = Node('Current', evaluate(position, side_to_move))
    first_moves = position.get_all_legal_moves_for_color(side_to_move)
    for first_move in first_moves:
        position_after_first_move = branch_from_position(position, first_move)
        all_legal_first_replies = position_after_first_move.get_all_legal_moves_for_color(opposite_color(side_to_move))
        if all_legal_first_replies:
            first_move_node = tree.add_child(first_move.generate_uci(), position_after_first_move)
            for first_reply in all_legal_first_replies:
                position_after_first_reply = branch_from_position(position_after_first_move, first_reply)
                all_legal_second_moves = position_after_first_reply.get_all_legal_moves_for_color(side_to_move)
                if all_legal_second_moves:
                    first_reply_node = first_move_node.add_child(f'{first_move_node.get_name()}-{first_reply.generate_uci()}', position_after_first_reply)
                    for second_move in all_legal_second_moves:
                        position_after_second_move = branch_from_position(position_after_first_reply, second_move)
                        all_legal_second_replies = position_after_second_move.get_all_legal_moves_for_color(opposite_color(side_to_move))
                        if all_legal_second_replies:
                            second_move_node = first_reply_node.add_child(f'{first_reply_node.get_name()}-{second_move.generate_uci()}', position_after_second_move)
                            for second_reply in all_legal_second_replies:
                                position_after_second_reply = branch_from_position(position_after_second_move, second_reply)
                                all_legal_third_moves = position_after_second_reply.get_all_legal_moves_for_color(side_to_move)
                                if all_legal_third_moves:
                                    second_move_node.add_child(f'{second_move_node.get_name()}-{second_reply.generate_uci()}', evaluate(position_after_second_reply, side_to_move))
                                else:
                                    if position_after_second_reply.is_under_check(side_to_move):
                                        second_move_node.add_child(f'{second_move_node.get_name()}-{second_reply.generate_uci()}', -1 * CHECKMATE_SCORE)
                                    else:
                                        second_move_node.add_child(
                                            f'{second_move_node.get_name()}-{second_reply.generate_uci()}',
                                            0)
                        else:
                            if position_after_second_move.is_under_check(opposite_color(side_to_move)):
                                first_reply_node.add_child(f'{first_reply_node.get_name()}-{second_move.generate_uci()}', CHECKMATE_SCORE)
                            else:
                                first_reply_node.add_child(f'{first_reply_node.get_name()}-{second_move.generate_uci()}',
                                                           0)
                else:
                    if position_after_first_reply.is_under_check(side_to_move):
                        first_move_node.add_child(f'{first_move_node.get_name()}-{first_reply.generate_uci()}',
                                                  -1 * CHECKMATE_SCORE)
                    else:
                        first_move_node.add_child(f'{first_move_node.get_name()}-{first_reply.generate_uci()}',
                                                  0)
        else:
            if position_after_first_move.is_under_check(opposite_color(side_to_move)):
                tree.add_child(first_move.generate_uci(), CHECKMATE_SCORE)
            else:
                tree.add_child(first_move.generate_uci(), 0)
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


def choose_best_move(position: Position) -> str:
    """
    Returns a UCI notation e.g. 'd1h5'
    :param position:
    :return:
    """
    tree = make_4_ply_move_tree(position)
    collapse_at_level(tree, 4, min)
    collapse_at_level(tree, 3, max)
    collapse_at_level(tree, 2, min)
    candidate_moves = tree.get_children()
    best_move = candidate_moves[0].get_name()
    best_score = candidate_moves[0].get_value()
    for move in candidate_moves:
        move_score = move.get_value()
        if move_score > best_score:
            best_score = move_score
            best_move = move.get_name()
    return best_move

