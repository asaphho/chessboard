from typing import List, Callable

from simple_bot.evaluation import evaluate


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

    def remove_all_children(self):
        self.children = []

    def get_name(self) -> str:
        return self.name

    def get_children(self) -> list:
        return self.children

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



