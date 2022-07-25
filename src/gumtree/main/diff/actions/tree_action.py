from abc import ABC

from src.gumtree.main.diff.actions.action import Action
from src.gumtree.main.trees.tree import Tree

class TreeAction(Action, ABC):
    def __init__(self, node: Tree):
        super().__init__(node)
        