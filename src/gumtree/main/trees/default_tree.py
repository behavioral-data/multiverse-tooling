from __future__ import annotations
import ast
from src.gumtree.main.trees.abstract_tree import AbstractTree
from src.gumtree.main.trees.tree_metrics import TreeMetrics

from typing import TYPE_CHECKING, Iterable, List

BOBA_VAR = 'BobaVar'

if TYPE_CHECKING:
    from src.gumtree.main.trees.tree import Tree

class DefaultTree(AbstractTree):
    def __init__(self, node_type: str, label: str = None):
        self._parent = None
        self._type = node_type
        self._label = label if label is not None else ""
        self._children = []
        self._metrics: TreeMetrics = None
        self._metadata = {}
   
    @classmethod 
    def init_from_other(cls, other: Tree) -> DefaultTree:
        tree = cls(other.node_type, other.label)
        return tree
    
    def deep_copy(self) -> Tree:
        copy = DefaultTree.init_from_other(self)
        for child in self.children:
            copy.add_child(child.deep_copy())
        return copy

class PythonTree(DefaultTree):
    def __init__(self, node_type: str, label: str =None,
                 ast_node: ast.AST=None):
        super().__init__(node_type, label)
        self._num_child_boba_var_nodes = 0
        self.ast_node: ast.AST = ast_node
        self.ast_code = ast.unparse(ast_node) if ast_node is not None else ""
    def ast_code(self):
        return ast.unparse(self.ast_node) if self.ast_node is not None else ""
    
class BobaTree(PythonTree):
    def __init__(self, node_type: str, label: str =None,
                ast_node: ast.AST=None):
        super().__init__(node_type, label, ast_node)
        self._num_child_boba_var_nodes = 0
        self._num_child_boba_vars = 0
        self.has_boba_var = False
    
    @property
    def num_child_boba_var_nodes(self) -> int: # number of boba var nodes in the child
       return self._num_child_boba_var_nodes 

    @num_child_boba_var_nodes.setter
    def num_child_boba_var_nodes(self, num_nodes: int):
        self._num_child_boba_var_nodes = num_nodes
        
    @property
    def num_child_boba_vars(self) -> int: # number of boba var nodes in the child
       return self._num_child_boba_vars 

    @num_child_boba_vars.setter
    def num_child_boba_vars(self, num_nodes: int):
        self._num_child_boba_vars = num_nodes
   
    @property
    def children(self) -> List[Tree]:
        return self._children
    
    @children.setter
    def children(self, child_list: List[BobaTree]):
        self._children = child_list
        for node in child_list:
            node.parent = self
        
        self.num_child_boba_var_nodes = sum(c.num_child_boba_var_nodes for c in child_list)
        self.num_child_boba_vars = sum(c.num_child_boba_vars for c in child_list)
        self.has_boba_var = any(c.node_type == BOBA_VAR for c in child_list) or any(c2.node_type == BOBA_VAR for c1 in child_list for c2 in c1.children)
        
    def post_order(self) -> Iterable[BobaTree]:
        return super().post_order()