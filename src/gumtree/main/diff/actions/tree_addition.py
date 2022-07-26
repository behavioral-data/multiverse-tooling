from abc import ABC
from re import L
from typing import Union

from src.gumtree.main.diff.actions.tree_action import TreeAction
from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.diff.actions.action import Action

class TreeAddition(TreeAction, ABC):
    def __init__(self, node: Tree, parent: Tree, pos: int):
        super().__init__(node)
        self._parent = parent
        self._pos = pos
        
    @property
    def parent(self) -> Tree:
        return self._parent
    
    @property
    def pos(self):
        return self._pos
    
    def __str__(self):
        node_str = str(self.parent) if self.parent is not None else "root"
        return f"===\n{self.get_name()}\n---\n{self.node.to_tree_string()}\nto\n{node_str}\nat {self.pos}"
    
    def __eq__(self, o: Union[TreeAction, Action]):
        if not(super().__eq__(o)):
            return False
        return self.parent == o.parent and self.pos == o.pos
    
class TreeInsert(TreeAddition):
    def get_name(self):
        return "insert-tree"