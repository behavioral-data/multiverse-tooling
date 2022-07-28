from __future__ import annotations

import ast
from typing import Iterable
from src.gumtree.main.trees.boba_tree_metrics_computer import BobaTreeMetricsComptuer
from src.gumtree.main.trees.default_tree import DefaultTree
from src.gumtree.main.trees.tree_metrics import BobaTreeMetrics
from src.gumtree.main.trees.tree_visitor import TreeVisitor

from src.gumtree.main.trees.node_constants import BOBA_VAR



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
        self._num_boba_var_nodes = 0

    def has_boba_var(self, height=2):
        return (self.tree_metrics.height_from_child_boba_var <= height 
                and self.tree_metrics.num_child_boba_vars > 0)
    
    @property
    def num_boba_var_nodes(self) -> int: # number of boba var nodes in the child
        if self.node_type == BOBA_VAR:
           return self._num_boba_var_nodes 
        else:
            return 0
       
    @num_boba_var_nodes.setter
    def num_boba_var_nodes(self, num_nodes: int):
        self._num_boba_var_nodes  = num_nodes
        
    @property
    def num_child_boba_var_nodes(self) -> int: # number of boba var nodes in the child
       return self.tree_metrics.num_child_boba_var_nodes
        
    @property
    def num_child_boba_vars(self) -> int: # number of boba var nodes in the child
       return self.tree_metrics.num_child_boba_vars
   
    @property
    def tree_metrics(self) -> BobaTreeMetrics:
        if self._metrics is None:
            root = self
            if not self.is_root():
                parents = self.get_parents()
                root = parents[-1]
            TreeVisitor.visit_tree(root, BobaTreeMetricsComptuer())
        return self._metrics
    
    @tree_metrics.setter
    def tree_metrics(self, metrics: BobaTreeMetrics):
        self._metrics = metrics
    
    def post_order(self) -> Iterable[BobaTree]:
        return super().post_order()