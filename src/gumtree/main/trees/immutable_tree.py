from src.gumtree.main.trees.abstract_tree import AbstractTree
from src.gumtree.main.trees.default_tree import DefaultTree

class ImmutableTree(AbstractTree):
    def deep_copy(self):
        copy = DefaultTree(self)
        for child in self.children:
            copy.add_child(child.deep_copy())
        return copy
    
    @AbstractTree.label.setter
    def label(self, lbl):
        raise NotImplementedError("This method should not be called on a ImmutableTree")
    
    @AbstractTree.node_type.setter
    def node_type(self, node_t):
        raise NotImplementedError("This method should not be called on a ImmutableTree")
    
    @AbstractTree.parent.setter
    def parent(self, node):
        raise NotImplementedError("This method should not be called on a ImmutableTree")
        
    