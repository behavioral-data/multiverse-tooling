
from abc import ABC, abstractmethod
from typing import Dict, List, Set, TYPE_CHECKING

from src.gumtree.main.matchers.mapping_store import MappingStore
from src.gumtree.main.matchers.matcher import Matcher
from src.gumtree.main.matchers.zs_matcher import ZsMatcher
from src.gumtree.main.trees.tree import Tree

class AbstractBottomUpMatcher(Matcher):
    DEFAULT_SIZE_THRESHOLD = 1000
    DEFAULT_SIM_THRESHOLD = 0.5
    
    def __init__(self):
        self.size_threshold = self.DEFAULT_SIZE_THRESHOLD
        self.sim_threshold = self.DEFAULT_SIM_THRESHOLD
        
    def configure(self, properties: Dict):
        self.size_threshold = properties.get('size_threshold', self.DEFAULT_SIZE_THRESHOLD)
        self.priority_calculator = properties.get('sim_threshold', self.DEFAULT_SIM_THRESHOLD)
        
    def get_dst_candidates(self, mappings: MappingStore, src: Tree) -> List[Tree]:
        seeds: List[Tree] = []
        for c in src.get_descendents():
            if mappings.is_src_mapped(c):
                seeds.append(mappings.get_dst_for_src(c))
        
        candidates: List[Tree] = []
        visited: Set[Tree] = set()
        for seed in seeds:
            while seed.parent is not None:
                parent = seed.parent
                if parent in visited:
                    break
                visited.add(parent)
                if (parent.node_type == src.node_type) and not(mappings.is_dst_mapped(parent) or parent.is_root()):
                    candidates.append(parent)
                seed = parent
        return candidates
        
    def last_chance_match(self, mappings: MappingStore, src: Tree, dst: Tree):
        if src.tree_metrics.size < self.size_threshold or dst.tree_metrics.size < self.size_threshold:
            m = ZsMatcher()
            zs_mappings = m.match(src, dst, MappingStore(src, dst))
            for candidate in zs_mappings:
                src_cand = candidate[0]
                dst_cand = candidate[1]
                if mappings.is_mapping_allowed(src_cand, dst_cand):
                    mappings.add_mapping(src_cand, dst_cand)
        # TODO see the ZsMatcher.java for impl
        