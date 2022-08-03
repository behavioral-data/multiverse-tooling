from __future__ import annotations
from abc import ABC, abstractmethod
from src.gumtree.main.trees.tree_context import TreeContext


class TreeGenerator(ABC):
    @abstractmethod
    def generate_tree(self, src_code, metadata=None) -> TreeContext:
        pass
    
    def generate_tree_from_file(self, file_path, metadata=None) -> TreeContext:
        with open(file_path, 'r') as f:
            src_code = f.read()
        return self.generate_tree(src_code, metadata=metadata)
    