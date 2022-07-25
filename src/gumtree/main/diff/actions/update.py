from src.gumtree.main.diff.actions.action import Action
from src.gumtree.main.trees.tree import Tree

class Update(Action):
    def __init__(self, node: Tree, value: str):
        super().__init__(node)
        self.value = value
        
    def get_name(self):
        return "update-node"

    def get_value(self):
        return self.value
    
    def __str__(self):
        return f"===\n{self.get_name()}\n---\n{str(self.node)}\nreplace {self.node.label} by {self.get_value()}"
    
    def __eq__(self, o):
        if not super().__eq__(o):
            return False
        a: Update = o
        return self.value == a.value