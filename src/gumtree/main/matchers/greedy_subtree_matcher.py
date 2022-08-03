from typing import List, Tuple, Set
from src.gumtree.main.matchers.abstract_subtree_matcher import AbstractSubtreeMatcher
from src.gumtree.main.matchers.mapping_comparators import (
    FullMappingComparator, 
    compare,
    cmp_to_key
)
from src.gumtree.main.trees.tree import Tree

class GreedySubtreeMatcher(AbstractSubtreeMatcher):
    def handle_ambiguous_mappings(self, ambiguous_mappings: List[Tuple[Set[Tree], Set[Tree]]]):
        comparator = FullMappingComparator(self.mappings)        
        ambiguous_mappings.sort(key=cmp_to_key(AmbiguousMappingComparator().compare))
        for pair in ambiguous_mappings:
            candidates = self.convert_to_mappings(pair)
            candidates.sort(key=cmp_to_key(comparator.compare)) 
            for mapping in candidates:
                if self.mappings.are_both_unmapped(mapping[0], mapping[1]):
                    self.mappings.add_mapping_recursively(mapping[0], mapping[1]) #line 23 in alg 1
        
    def convert_to_mappings(self, ambiguous_mapping: Tuple[Set[Tree], Set[Tree]]):
        mappings = []
        for src in ambiguous_mapping[0]:
            for dst in ambiguous_mapping[1]:
                mappings.append((src, dst))
        return mappings
        
class AmbiguousMappingComparator: 
    """
    Sort based on the set of trees that contain the largest size
    """
    def compare(self, m1: Tuple[Set[Tree], Set[Tree]], m2: Tuple[Set[Tree], Set[Tree]]):
        s1 = max(m1[0], key=lambda tree: tree.tree_metrics.size).tree_metrics.size
        s2 = max(m1[0], key=lambda tree: tree.tree_metrics.size).tree_metrics.size
        return compare(s2, s1)