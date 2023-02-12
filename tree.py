import networkx as nx
from functools import cached_property
from itertools import chain
from math import exp, sqrt
from pricer import Option, Underlying
from node import Node
from utils import remove_dupnan, create_network_graph
from typing import List


class TrinomialTree:
    EPSILON = 10**-10
    MULTIPLICATOR = sqrt(3)

    def __init__(self, option: Option, underlying: Underlying):
        self.option = option
        self.underlying = underlying
        self._nodes = []

    def __len__(self):
        return self.option.steps

    def _seed(self) -> List[Node]:
        self.root = self._add_node(parent=None, price=self.underlying.spot_price)
        forward_price = self.root.underlying_price * exp(self.underlying.interest_rate * self.option.time_delta)
        self.root.child_up = self._add_node(parent=self.root, price=forward_price * self.alpha)
        self.root.child_mid = self._add_node(parent=self.root, price=forward_price)
        self.root.child_down = self._add_node(parent=self.root, price=forward_price / self.alpha)
        self.root.proba.cum = 1
        self.root.compute_probas()
        self._nodes.append([self.root])
        return [self.root.child_up, self.root.child_mid, self.root.child_down]

    @cached_property
    def alpha(self) -> float:
        return exp((self.underlying.interest_rate * self.option.time_delta) + (self.underlying.volatility * self.MULTIPLICATOR * sqrt(self.option.time_delta)))

    def create(self, pruning=True) -> None:
        next_col = self._seed()
        self._nodes.append(next_col)
        for _ in range(self.option.steps - 1):
            parent_col = next_col.copy()
            _ = list(chain(*map(self._add_branches, parent_col)))
            child_col = list(chain(*map(self._add_edges, parent_col)))
            child_col = remove_dupnan(child_col)
            [node.compute_probas() for node in parent_col]
            if pruning:
                next_col = list(chain(*map(self._chop_off, child_col)))
                next_col = remove_dupnan(next_col)
            else:
                next_col = remove_dupnan(child_col)
            self._nodes.append(next_col)
        self.leafs = next_col

    def _add_node(self, parent: Node, price: float) -> Node:
        return Node(parent=parent, underlying_price=price, option=self.option)

    def _add_branches(self, node: Node) -> List[Node]:
        forward_price = node.underlying_price * exp(self.underlying.interest_rate * self.option.time_delta)
        node.child_mid = self._add_node(parent=node, price=forward_price)
        if node.is_elder or (node.parent.child_up is None):
            node.child_up = self._add_node(parent=node, price=forward_price * self.alpha)
        elif node.is_benjamin or (node.parent.child_down is None):
            node.child_down = self._add_node(parent=node, price=forward_price / self.alpha)
        return [node.child_up, node.child_mid, node.child_down]

    def _add_edges(self, node: Node) -> List[Node]:
        if node.is_cadet:
            node.child_up = node.parent.child_up.child_mid if not node.child_up else node.child_up
            node.child_down = node.parent.child_down.child_mid if not node.child_down else node.child_down
        elif node.is_elder:
            node.child_down = node.parent.child_mid.child_mid
        elif node.is_benjamin:
            node.child_up = node.parent.child_mid.child_mid
        return [node.child_up, node.child_mid, node.child_down]

    def _chop_off(self, node: Node) -> List[Node]:
        if node.proba.cum < self.EPSILON:
            node.parent.proba.up = node.parent.proba.down = 0
            node.parent.proba.mid = 1
            if not node.is_benjamin:
                node.parent.child_up = None
            elif not node.is_elder:
                node.parent.child_down = None
            del node
            return [None]
        else:
            return [node]

    def _calc_node_value(self, node: Node) -> List[Node]:
        node.nfv = node.compute_value()
        return remove_dupnan([node.parent])

    def compute_price(self) -> None:
        nodes_column = self.leafs
        while nodes_column:
            nodes_column = list(set(chain(*map(self._calc_node_value, nodes_column))))

    def to_graph(self) -> nx.Graph:
        nodes = list(chain(*self._nodes))
        d = {n.underlying_price: [c.underlying_price for c in n.children] for n in nodes}
        G = nx.Graph(d)
        x_pos = [n.dt.timestamp() for n in nodes]
        y_pos = [n.underlying_price for n in nodes]
        pos = dict(zip(y_pos, list(zip(x_pos, y_pos))))
        nx.set_node_attributes(G, pos, "pos")
        caract = {n.underlying_price: [n.proba.cum, n.nfv] for n in nodes}
        nx.set_node_attributes(G, caract, "caract")
        return G

    def plot(self):
        G = self.to_graph()
        fig = create_network_graph(G)
        fig.show()
