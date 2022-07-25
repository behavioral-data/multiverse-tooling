from src.gumtree.main.diff.actions.tree_addition import TreeAction, TreeAddition
from src.gumtree.main.trees.tree import Tree
    
class Move(TreeAddition):
    def __init__(self, node: Tree, parent: Tree, pos: int):
        super().__init__(node, parent, pos)
        
    def get_name(self) -> str:
        return "move-tree"