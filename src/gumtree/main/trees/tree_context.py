from typing import TYPE_CHECKING

import src.gumtree.main.diff.io.tree_io_utils as tree_io_utils
from src.gumtree.main.trees.default_tree import DefaultTree
from src.gumtree.main.trees.fake_tree import FakeTree
from src.gumtree.main.trees.boba_tree import BobaTree


if TYPE_CHECKING:
    from src.gumtree.main.trees.tree import Tree
    
class TreeContext:
    def __init__(self):
        self.root: Tree = None
        self.metadata = {}
        
    def __str__(self):
        return str(tree_io_utils.to_text(self))
    
    def create_tree(self, node_type: str, label:str = None):
        return DefaultTree(node_type, label)
    
    def create_boba_tree(self, node_type: str, label: str=None):
        return BobaTree(node_type, label)
    
    def create_fake_tree(self, *trees):
        return FakeTree(*trees)
    
    def get_metadata(self, key: str):
        return self.metadata.get(key, None)
    
    def set_metadata(self, key: str, value):
        old_v = self.metadata.get(key, None)
        self.metadata[key] = value
        return old_v
    
    