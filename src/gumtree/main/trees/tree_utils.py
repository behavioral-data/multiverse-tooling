from __future__ import annotations

from collections import deque
from abc import ABC, abstractmethod
from typing import Deque, List, TYPE_CHECKING

from collections.abc import Iterator  # since python 3.3 Iterator is here

if TYPE_CHECKING:
    from src.gumtree.main.trees.tree import Tree
    
class HNIterator(Iterator):  # need to subclass Iterator rather than object
    def __init__(self, it):
        self.it = iter(it)
        self._hasnext = None
        
    def __iter__(self): 
        return self
    
    def __next__(self):        # __next__ vs next in python 2
        if self._hasnext:
            result = self._thenext
        else:
            result = next(self.it)
        self._hasnext = None
        return result
    
    def has_next(self):
        if self._hasnext is None:
            try: 
                self._thenext = next(self.it)
            except StopIteration: 
                self._hasnext = False
            else: self._hasnext = True
        return self._hasnext


class TreeIterator(ABC):
    def __init__(self):
       self.stack: Deque[HNIterator] = deque()
       
    @abstractmethod 
    def __iter__(self):
        pass
    
    @abstractmethod
    def has_next(self) -> bool:
        pass
     
    @abstractmethod   
    def __next__(self):
        pass
    
    @abstractmethod
    def push(self):
        pass
    
    @abstractmethod
    def remove(self):
        pass

class PreOrderIterator(TreeIterator):
    # missing root node
    
    def __init__(self, node):
        super().__init__()
        from src.gumtree.main.trees.fake_tree import FakeTree
        self.push(FakeTree(node))
        
    def __iter__(self):
        return self
    
    def __next__(self) -> Tree:
        if len(self.stack) == 0:
            raise StopIteration
        it = self.stack[-1]
        tree = next(it, None)
        while it is not None and not it.has_next():
            self.stack.pop()
            it = self.stack[-1] if self.stack else None
        
        self.push(tree)
        return tree
    
    def push(self, tree: Tree):
        if not tree.is_leaf():
            self.stack.append(HNIterator(tree.children))
            
    def has_next(self) -> bool:
        return len(self.stack) > 0
    
    def remove(self):
        raise NotImplementedError
    
class PostOrderIterator(TreeIterator):
    
    def __init__(self, node: Tree):
        super().__init__()
        self.push(node)
        
    def __iter__(self):
        return self
    
    def __next__(self) -> Tree:
        if len(self.stack) == 0:
            raise StopIteration
        return self.select_next_child(self.stack[-1][1])
        
    def has_next(self) -> bool:
        return len(self.stack) > 0
    
    def select_next_child(self, it: HNIterator[Tree]) -> Tree:
        if not it.has_next():
            return self.stack.pop()[0]
        item = next(it)
        if item.is_leaf():
            return item
        return self.select_next_child(self.push(item))
    
    def push(self, item: Tree):
        it = HNIterator(item.children)
        self.stack.append((item, it))
        return it
    
    def remove(self):
        raise NotImplementedError
  
def post_order(tree: Tree) -> List[Tree]:
    trees = []
    post_order_helper(tree, trees)
    return trees

def post_order_helper(tree: Tree, trees: List[Tree]):
    if not tree.is_leaf():
        for c in tree.children:
            post_order_helper(c, trees)
    trees.append(tree)
    
    
def preorder(tree: Tree) -> List[Tree]:
    trees = []
    preorder_w_list(tree, trees)
    return trees

def preorder_w_list(tree: Tree, trees: List[Tree]):
    trees.append(tree)
    if not tree.is_leaf():
        for c in tree.children:
            preorder_w_list(c, trees)
            
def breadth_first(tree: Tree):
    trees: List[Tree] = []
    currents: List[Tree] = []
    currents.append(tree)
    while len(currents) > 0:
        c = currents.pop(0)
        trees.append(c)
        currents.extend(c.children)
    return trees