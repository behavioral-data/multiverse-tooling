from __future__ import annotations

import re
from typing import Iterable, List, Dict
from abc import ABC, abstractmethod
from src.gumtree.main.trees.tree_utils import PreOrderIterator, PostOrderIterator, preorder
from src.gumtree.main.trees.tree_metrics import TreeMetrics

  
class Tree(ABC):
        
    url_pattern = re.compile("\\d+(\\.\\d+)*")
    
    def get_child_from_url(self, url):
        if not self.url_pattern.match(url):
            raise ValueError("Wrong URL format : " + url)

        path = url.split('.')
        node = self
        while path:
            child_pos = int(path[0]) if type(path) is list else int(path)
            path = path[1:]
            node = node.children[child_pos]
        return node
    

    @property
    def num_child_boba_var_nodes(self) -> int: # number of boba var nodes in the child
       return 0
   
    @property
    def num_child_boba_vars(self) -> int: # number of boba var nodes in the child
       return 0
    
    @property
    @abstractmethod
    def pos(self) -> int:
        pass 
    
    @pos.setter
    @abstractmethod
    def pos(self, p: int):
        pass
    
    @property
    @abstractmethod
    def length(self) -> int:
        pass 
    
    @pos.setter
    @abstractmethod
    def length(self, l: int):
        pass
    
    @property
    def end_pos(self):
        return self.pos + self.length
    
    @property    
    @abstractmethod
    def metadata(self) -> Dict:
        pass
    
    @metadata.setter
    @abstractmethod
    def metadata(self):
        pass
    
    @abstractmethod
    def deep_copy(self) -> Tree:
        pass
    
    @property    
    @abstractmethod
    def label(self) -> List:
        pass
    
    @label.setter
    @abstractmethod
    def label(self):
        pass
    
    @property    
    @abstractmethod
    def node_type(self) -> List:
        pass
    
    @node_type.setter
    @abstractmethod
    def node_type(self):
        pass
    
    @property    
    @abstractmethod
    def children(self) -> List[Tree]:
        pass
    
    @children.setter
    @abstractmethod
    def children(self):
        pass
    
    @property    
    @abstractmethod
    def parent(self) -> Tree:
        pass
    
    @parent.setter
    @abstractmethod
    def parent(self):
        pass
    
    @property    
    @abstractmethod
    def tree_metrics(self) -> TreeMetrics:
        pass
    
    @tree_metrics.setter
    @abstractmethod
    def tree_metrics(self):
        pass
    
    @abstractmethod
    def add_child(self):
        pass
    
    @abstractmethod
    def insert_child(self, t: Tree, position: int):
        pass
    
    @abstractmethod
    def to_tree_string(self) -> str:
        pass
    
    @abstractmethod
    def viz_graph(self, save_path: str):
        pass
    
    def get_parents(self) -> List[Tree]:
        parents = []
        if self.parent is None:
            return parents
        else:
            parents.append(self.parent)
            parents.extend(self.parent.get_parents())
        return parents
    
    def get_child_position(self, child: Tree) -> Tree:
        try:
            return self.children.index(child)
        except ValueError as e:
            return -1
        
    def is_root(self):
        return self.parent is None
    
    def is_leaf(self):
        return len(self.children) == 0 
    
    def has_same_type(self, t: Tree):
        return t.node_type == self.node_type
    
    def has_same_type_and_label(self, t: Tree):
        return self.has_same_type(t) and self.label == t.label
    
    
    def is_isomorphic_to(self, tree: Tree):
        if not self.has_same_type_and_label(tree):
            return False
        if len(self.children) != len(tree.children):
            return False
        
        for i, child in enumerate(self.children):
            is_children_isomorphic = child.is_isomorphic_to(tree.children[i])
            if not is_children_isomorphic:
                return False
        
        return True
    
    def is_isostructural_to(self, tree: Tree):
        if self.node_type != tree.node_type:
            return False
        if len(self.children) != len(tree.children):
            return False
        
        for i, child in enumerate(self.children):
            is_children_structural = child.is_isostructural_to(tree.children[i])
            if not is_children_structural:
                return False
        return True
    
    def get_descendents(self):
        trees = preorder(self)
        trees.pop(0)
        return trees
      
    def pre_order(self) -> Iterable[Tree]:
        iterator = PreOrderIterator(self) 
        return iterator
    
    def post_order(self) -> Iterable[Tree]:
        iterator = PostOrderIterator(self)
        return iterator
    
    def position_in_parent(self) -> int:
        p = self.parent
        if p is None:
            return -1
        else:
            return p.children.index(self)
        
    def search_subtree(self, subtree: Tree):
        results = []
        for candidate in self.pre_order():
            if candidate.tree_metrics.hashcode == subtree.tree_metrics.hashcode:
                if candidate.is_isomorphic_to(subtree):
                    results.append(candidate)     
        return results