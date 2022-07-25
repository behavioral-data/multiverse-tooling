from __future__ import annotations

from typing import TYPE_CHECKING
from src.gumtree.main.trees.abstract_tree import AbstractTree
from src.gumtree.main.trees.tree_metrics import TreeMetrics

if TYPE_CHECKING:
    from src.gumtree.main.trees.tree import Tree
    
class FakeTree(AbstractTree):
    def __init__(self, *trees):
        self.children = list(trees)
        self._label = ""
        self._metrics: TreeMetrics = None
        self._type = ""
        self.metadata = {}
        
    def deep_copy(self) -> Tree:
        copy = FakeTree()
        for child in self.children:
            copy.add_child(child.deep_copy())
        return copy
        
    @AbstractTree.label.setter
    def label(self, lbl):
        raise NotImplementedError("This method should not be called on a FakeTree")
    
    @AbstractTree.node_type.setter
    def node_type(self, node_t):
        raise NotImplementedError("This method should not be called on a FakeTree")
    
    def __str__(self):
        return "FakeTree"