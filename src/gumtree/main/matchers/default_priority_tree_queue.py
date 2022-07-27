from __future__ import annotations

from typing import Callable, List, TYPE_CHECKING
from xmlrpc.client import boolean
from pqdict import pqdict
if TYPE_CHECKING:
    from src.gumtree.main.trees.tree import Tree

class DefaultPriorityTreeQueue:
    HEIGHT_PRIORITY_CALCULATOR: Callable[[Tree], int] = lambda tree: tree.tree_metrics.height
    SIZE_PRIORITY_CALCULATOR: Callable[[Tree], int]= lambda tree: tree.tree_metrics.size
    
    @staticmethod
    def get_priority_calculator(name):
        if name == 'size':
            return DefaultPriorityTreeQueue.SIZE_PRIORITY_CALCULATOR
        else:
            return DefaultPriorityTreeQueue.HEIGHT_PRIORITY_CALCULATOR
    
    def __init__(self, root: Tree,
                 minimum_priority: int,
                 priority_calculator: Callable[[Tree], int]):
        self.trees_pq = pqdict(key=lambda x: x[0], reverse=True) # prioirty to Tuple[prioirty, List[Tree]]
        self.minimum_priority = minimum_priority
        self.priority_calculator = priority_calculator
        self.add(root)
    
    def pop_open(self) -> List[Tree]:
        trees_popped = self.pop()
        for t in trees_popped:
            self.open(t)
        return trees_popped
    
    def pop(self) -> List[Tree]:
        return self.trees_pq.pop(self.current_priority())[1]
    
    def open(self, tree: Tree):
        for c in tree.children:
            self.add(c)
    
    def current_priority(self):
        return self.trees_pq.top()
    
    def is_empty(self):
        return len(self.trees_pq) == 0
    
    def clear(self):
        self.trees_pq = pqdict(key=lambda x: x[0], reverse=True)
    
    def add(self, t: Tree):
        priority = self.priority_calculator(t)
        # * temperorary custom code for Python, if want to include other languages need to generalize
        if priority < self.minimum_priority and t.node_type in ['Load', 'Store']:  
            return
        
        if priority not in self.trees_pq:
            self.trees_pq.additem(priority, (priority, []))
        self.trees_pq[priority][1].append(t)
        
    @staticmethod
    def synchronize(q1: DefaultPriorityTreeQueue, q2: DefaultPriorityTreeQueue ) -> boolean:
        while (not(q1.is_empty() or q2.is_empty()) and q1.current_priority() != q2.current_priority()):
            if q1.current_priority() > q2.current_priority():
                q1.pop_open()
            else:
                q2.pop_open()
            
        if q1.is_empty() or q2.is_empty():
            q1.clear()
            q2.clear()
            return False
        else:
            return True