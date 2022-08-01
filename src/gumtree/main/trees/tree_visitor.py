from __future__ import annotations
from abc import ABC, abstractmethod
import json
from typing import Callable
import zlib
from src.gumtree.main.trees.tree_metrics import TreeMetrics
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.gumtree.main.trees.tree import Tree

hash_func = lambda x: zlib.adler32(json.dumps(x).encode("utf8"))

class TreeVisitor(ABC):
    @staticmethod
    def visit_tree(root: Tree, tree_visitor: TreeVisitor,
                   start_tree_func: Callable[[Tree]]=None,
                   end_tree_func: Callable[[Tree]]=None):
        stack = []
        stack.append([root, iter(root.children)])
        
        tree_visitor.call_start_tree(root, start_tree_func)
        while stack:
            tree, tree_children = stack[-1]
            next_child = next(tree_children, None)
            if next_child is None:
                tree_visitor.call_end_tree(tree, end_tree_func)
                stack.pop()
            else:
                stack.append([next_child, iter(next_child.children)])
                tree_visitor.call_start_tree(next_child, start_tree_func)
    
    def call_start_tree(self, tree: Tree, 
                        start_tree_func: Callable[[Tree]]=None):
        if start_tree_func is not None:
            start_tree_func(tree)
        else:
            self.start_tree(tree)
    
    def call_end_tree(self, tree: Tree,
                      end_tree_func: Callable[[Tree]]=None):
        if end_tree_func is not None:
            end_tree_func(tree)
        else:
            self.end_tree(tree)
     
    @abstractmethod
    def start_tree(self, tree: Tree):
        pass
    
    @abstractmethod
    def end_tree(self, tree: Tree):
        pass
    
class DefaultTreeVisitor(TreeVisitor):
    def start_tree(self, tree: Tree):
        return None
    
    def end_tree(self, tree: Tree):
        return None

class InnerNodesAndLeavesVisitor(TreeVisitor, ABC):
    def start_tree(self, tree: Tree):
        if tree.is_leaf():
            self.visit_leaf(tree)
        else:
            self.start_inner_node(tree)
            
    def end_tree(self, tree: Tree):
        if not tree.is_leaf():
            self.end_inner_node(tree)
    
    @abstractmethod
    def start_inner_node(self, tree: Tree):
        pass
    
    @abstractmethod
    def end_inner_node(self, tree: Tree):
        pass
    
    @abstractmethod
    def visit_leaf(self, tree: Tree):
        pass
    
    
class TreeMetricComputer(InnerNodesAndLeavesVisitor):
    ENTER = "enter"
    LEAVE = "leave"
    BASE = 33
    
    def __init__(self):
        self.current_depth = 0
        self.current_position = 0
    
    def start_inner_node(self, tree: Tree):
        self.current_depth += 1
    
    def visit_leaf(self, tree: Tree):
        tree.tree_metrics = TreeMetrics(size=1,
                                   height=0, 
                                   hashcode=self.leaf_hash(tree),
                                   structure_hash=self.leaf_structure_hash(tree),
                                   depth=self.current_depth,
                                   position=self.current_position)
        self.current_position += 1
        
    def end_inner_node(self, tree: Tree):
        self.current_depth -= 1
        sum_size = 0
        max_height = 0
        current_hash = 0
        current_structure_hash = 0
        for child in tree.children: 
            metrics = child.tree_metrics
            exponent = 2 * sum_size + 1
            current_hash += metrics.hashcode * self.hash_factor(exponent)
            current_structure_hash += metrics.structure_hash * self.hash_factor(exponent)
            sum_size += metrics.size
            if metrics.height > max_height:
                max_height = metrics.height
        
        tree.tree_metrics = TreeMetrics(size=sum_size + 1,
                                        height=max_height + 1,
                                        hashcode=self.inner_node_hash(tree, 2 * sum_size + 1, current_hash),
                                        structure_hash=self.inner_node_structure_hash(tree, 2 * sum_size + 1, current_structure_hash),
                                        depth=self.current_depth,
                                        position=self.current_position
        )
        self.current_position += 1
        
        
    def hash_factor(self, exponent):
        return self.BASE ** exponent
    
    def inner_node_hash(self, tree: Tree, size: int, middle_hash: int):
        return (hash_func((tree.node_type, tree.label, self.ENTER)) 
                + middle_hash 
                + hash_func((tree.node_type, tree.label, self.LEAVE)) * (self.hash_factor(size)))
        
    def inner_node_structure_hash(self, tree: Tree, size: int, middle_hash: int):
        return (hash_func((tree.node_type, self.ENTER)) 
                + middle_hash 
                + hash_func((tree.node_type, self.LEAVE)) * (self.hash_factor(size)))
    
    def leaf_hash(self, tree: Tree):
        return self.inner_node_hash(tree, size=1, middle_hash=0)
    
    def leaf_structure_hash(self, tree: Tree):
        return self.inner_node_structure_hash(tree, size=1, middle_hash=0)