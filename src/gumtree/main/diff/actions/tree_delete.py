from src.gumtree.main.diff.actions.tree_action import TreeAction


class TreeDelete(TreeAction):
    def get_name(self):
        return "delete-tree"
    
    def __str__(self):
        return f"===\n{self.get_name()}\n---\n{self.node.to_tree_string()}"