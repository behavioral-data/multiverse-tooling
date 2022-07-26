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
    
class PythonTreeGenerator(TreeGenerator):
    
    @staticmethod
    def get_node_label(node: ast.AST):
        labels = []
        skip_fields = ["lineno", "col_offset", "end_lineno", "end_col_offset"]
        for field, value in list(ast.iter_fields(node)):
            if (type(value) is int or type(value) is str) and field not in skip_fields:
                labels.append(f"{field}={value}")
        return ", ".join(labels)
    
    @staticmethod
    def get_node_type(node: ast.AST):
        return node.__class__.__name__
    
    def generate_tree(self, src_code: str, metadata=None) -> TreeContext:
        ast_node = ast.parse(src_code)
        tree = self.generate_tree_helper(ast_node)
        tree_ctx = TreeContext()
        tree_ctx.root = tree
        
        if metadata is not None and type(metadata) is dict:
            for k, v in metadata.items():
                tree_ctx.set_metadata(k, v)
        return tree_ctx
        
    def generate_tree_helper(self, ast_node: ast.AST) -> Tree:
        nv = NodeVisitorStack()
        node = DefaultTree(self.get_node_type(ast_node), self.get_node_label(ast_node))        
        children = nv.get_children(ast_node)
        tree_children = [self.generate_tree_helper(child) for child in children]
        node.children = tree_children
        return node
        