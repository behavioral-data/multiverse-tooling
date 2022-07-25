from collections import defaultdict
from typing import (
    List,
    Set,
    Dict,
    Tuple
)
from src.gumtree.main.trees.tree import Tree

class HashBasedMapper:
    def __init__(self) -> None:
        self.mappings: Dict[int, ] = defaultdict(lambda: (set(), set()))
    
    def add_srcs(self, trees: List[Tree]):
        for tree in trees:
            self.add_src(tree)
    
    def add_dsts(self, trees: List[Tree]):
        for tree in trees:
            self.add_dst(tree)
            
    def add_src(self, src: Tree):
        self.mappings[src.tree_metrics.hashcode][0].add(src)
        
    def add_dst(self, dst: Tree):
        self.mappings[dst.tree_metrics.hashcode][1].add(dst)

    def unique(self) -> List[Tuple[Set[Tree], Set[Tree]]]:
        return filter(lambda x: len(x[0]) ==  1 and len(x[1]) == 1,
                      self.mappings.values())
    
    def ambiguous(self) -> List[Tuple[Set[Tree], Set[Tree]]]:
        return filter(lambda x: (len(x[0]) >  1 and len(x[1]) >= 1) or (len(x[0]) >= 1 and len(x[1]) > 1),
                      self.mappings.values())
        
    def unmapped(self) -> List[Tuple[Set[Tree], Set[Tree]]]:
        return filter(lambda x: len(x[0]) == 0 or len(x[1]) == 0, self.mappings.values())
    
    def is_src_mapped(self, src: Tree):
        return len(self.mappings[src.tree_metrics.hashcode][1]) > 0
    
    def is_dst_mapping(self, dst: Tree):
        return len(self.mappings[dst.tree_metrics.hashcode][0]) > 0