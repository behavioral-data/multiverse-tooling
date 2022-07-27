from abc import ABC, abstractmethod
import ast
from src.gumtree.main.trees.tree_context import TreeContext
from src.ast_traverse import NodeVisitorStack
from src.gumtree.main.trees.default_tree import DefaultTree
from src.gumtree.main.trees.tree import Tree



class TreeGenerator(ABC):
    @abstractmethod
    def generate_tree(self, src_code, metadata=None) -> TreeContext:
        pass
    
    def generate_tree_from_file(self, file_path, metadata=None) -> TreeContext:
        with open(file_path, 'r') as f:
            src_code = f.read()
        return self.generate_tree(src_code, metadata=metadata)
    