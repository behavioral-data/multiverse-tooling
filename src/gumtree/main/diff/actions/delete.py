from src.gumtree.main.diff.actions.action import Action
from src.gumtree.main.trees.tree import Tree


class Delete(Action):
    def __init__(self, node: Tree):
        super().__init__(node)
        
    def get_name(self):
        return "delte-node"

    def __str__(self):
        return f"===\n{self.get_name()}\n---\n{self.node}\n==="