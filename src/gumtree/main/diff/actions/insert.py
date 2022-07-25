from src.gumtree.main.diff.actions.addition import Addition
from src.gumtree.main.trees.tree import Tree

class Insert(Addition):
    def __init__(self, node: Tree, parent: Tree, pos: int):
        super().__init__(node, parent, pos)
        
    def get_name(self):
        return "insert-node"