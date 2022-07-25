from abc import ABC
from typing import Union 
from src.gumtree.main.diff.actions.action import Action

from src.gumtree.main.trees.tree import Tree


class Addition(Action, ABC):
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
        return f"===\n{self.get_name()}\n---\n{self.node}\nto\n{node_str}\nat {self.pos}"
    
    def __eq__(self, o: Union[Action, Action]):
        if not(super().__eq__(o)):
            return False
        return self.parent == o.parent and self.pos == o.pos