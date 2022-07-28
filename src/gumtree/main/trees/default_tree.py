from __future__ import annotations
from src.gumtree.main.trees.abstract_tree import AbstractTree
from src.gumtree.main.trees.tree_metrics import TreeMetrics

from typing import TYPE_CHECKING, Iterable, List

if TYPE_CHECKING:
    from src.gumtree.main.trees.tree import Tree

class DefaultTree(AbstractTree):
    def __init__(self, node_type: str, label: str = None):
        self._parent = None
        self._type = node_type
        self._label = label if label is not None else ""
        self._children = []
        self._metrics: TreeMetrics = None
        self._metadata = {}
   
    @classmethod 
    def init_from_other(cls, other: Tree) -> DefaultTree:
        tree = cls(other.node_type, other.label)
        return tree
    
    def deep_copy(self) -> Tree:
        copy = DefaultTree.init_from_other(self)
        for child in self.children:
            copy.add_child(child.deep_copy())
        return copy

