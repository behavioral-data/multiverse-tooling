from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.gumtree.main.trees.tree import Tree

class Action(ABC):
    def __init__(self, node: Tree):
        self._node = node
    
    @property
    def node(self) -> Tree:
        return self._node
    
    @node.setter
    def node(self, new_node: Tree):
        self._node = new_node
    
    @abstractmethod
    def get_name(self):
        pass
    
    def __eq__(self, o: Action):
        if super().__eq__(o):
            return True
        elif o is None:
            return False
        elif o.__class__.__name__ != self.__class__.__name__:
            return False

        return self.node == o.node