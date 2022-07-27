from abc import ABC
import ast
from typing import List, Dict

from src.gumtree.main.trees.tree_metrics import TreeMetrics
from src.gumtree.main.trees.tree_visitor import TreeMetricComputer, TreeVisitor
from src.ast_traverse import NodeVisitorStack
import src.gumtree.main.diff.io.tree_io_utils as tree_io_utils

from src.gumtree.main.trees.tree import Tree

def get_node_label(node: ast.AST):
    labels = []
    skip_fields = ["lineno", "col_offset", "end_lineno", "end_col_offset"]
    for field, value in list(ast.iter_fields(node)):
        if (type(value) is int or type(value) is str) and field not in skip_fields:
            labels.append(f"{field}={value}")
    return ", ".join(labels)
            

class AbstractTree(Tree, ABC):
    def __init__(self, node: ast.AST, parent=None):
        self._parent = parent
        self._children = []
        self._metrics: TreeMetrics = None
        self._type = node.__class__.__name__
        self._label = get_node_label(node)
        self._metadata = {}
        
    def __repr__(self):
        
        if self.label:
            return f"{self.__class__.__name__}: {self.node_type} ({self.label}) "
        else:
            return f"{self.__class__.__name__}: {self.node_type}"
    @property    
    def metadata(self) -> Dict:
        if not hasattr(self, "_metadata"):
            self._metadata = {}
        return self._metadata
    
    @metadata.setter
    def metadata(self, md: Dict):
        self._metadata = md
    
    @property    
    def label(self) -> List:
        if not hasattr(self, "_label"):
            self._label = ""
        return self._label
    
    @label.setter
    def label(self, lbl):
        self._label = lbl
    
    @property    
    def node_type(self) -> List:
        if not hasattr(self, "_type"):
            self._type = ""
        return self._type

    @node_type.setter
    def node_type(self, node_t):
        self._type = node_t
    
    @classmethod
    def init_from_ast_tree(cls, ast_node: ast.AST, parent=None):
        children = NodeVisitorStack.get_children(ast_node)
        node = cls(ast_node, parent)
        tree_children = [cls.init_from_ast_tree(child, node) for child in children]
        node.children = tree_children
        return node
            
    def add_child(self, child: Tree):
        self.children.append(child)
        child.parent = self
    
    def insert_child(self, child: Tree, position: int):
        self.children.insert(position, child)
        child.parent = self
    
    def set_parent_and_update_children(self, parent: Tree):
        if self.parent is not None:
            try:
                self.parent.children.remove(self)
            except ValueError as e:
                pass
        self.parent = parent
        if self.parent is not None:
            parent.children.append(self)
    
    @property
    def tree_metrics(self):
        if self._metrics is None:
            root = self
            if not self.is_root():
                parents = self.get_parents()
                root = parents[-1]
            TreeVisitor.visit_tree(root, TreeMetricComputer())
        return self._metrics
    
    @tree_metrics.setter
    def tree_metrics(self, metrics: TreeMetrics):
        self._metrics = metrics
    
    @property
    def children(self) -> List[Tree]:
        return self._children

    @children.setter
    def children(self, child_list: List[Tree]):
        self._children = child_list
        for node in child_list:
            node.parent = self
            
    @property
    def parent(self):
        if not hasattr(self,"_parent"):
            self._parent = None
        return self._parent
    
    @parent.setter
    def parent(self, node):
        self._parent = node
        
    def to_tree_string(self):
        return str(tree_io_utils.to_short_text(self))
        
    
if __name__ == '__main__':
    code = """#!/usr/bin/env python3
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
# --- (BOBA_CONFIG)
{
  "graph": [
    "NMO1->ECL1->A",
    "NMO2->ECL2->A",
    "NMO1->A",
    "NMO2->A",
    "A->B",
    "A->EC->B"
  ],
  "decisions": [
    {"var": "fertility_bounds", "options": [
      [[7, 14], [17, 25], [17, 25]],
      [[6, 14], [17, 27], [17, 27]],
      [[9, 17], [18, 25], [18, 25]],
      [[8, 14], [1, 7], [15, 28]],
      [[9, 17], [1, 8], [18, 28]]
    ]},
    {"var": "relationship_bounds",
      "options": [[2, 3], [1, 2], [1, 3]]}
  ],
  "before_execute": "cp ../durante_etal_2013_study1.txt ./code/"
}
# --- (END)
"""

    tree = AbstractTree.init_from_ast_tree(ast.parse(code))
    child = tree.get_child_from_url('2.0')
    metrics = child.tree_metrics
    iterator_pre = tree.pre_order()
    iterator_post = tree.post_order()
    print('here')