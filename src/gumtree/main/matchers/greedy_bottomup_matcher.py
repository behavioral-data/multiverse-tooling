import ast
from typing import Dict, List, Set
from src.gumtree.main.matchers.abstract_bottom_up_matcher import AbstractBottomUpMatcher
from src.gumtree.main.matchers.mapping_store import MappingStore
import src.gumtree.main.matchers.similarity_metrics as similarity_metrics
from src.gumtree.main.trees.tree import Tree

from src.gumtree.main.trees.boba_tree import BobaTree
from src.gumtree.main.trees.node_constants import BOBA_VAR



class GreedyBottomUpMatcher(AbstractBottomUpMatcher):
    def match(self, src: Tree, dst: Tree, mappings: MappingStore) -> MappingStore:
        for t in src.post_order(): # line 1 in alg 2
            if t.is_root():
                mappings.add_mapping(t, dst)
                self.last_chance_match(mappings, t, dst)
                break
            elif not(mappings.is_src_mapped(t) or t.is_leaf()): # t1 is not matched and t1 has children, line 1 in alg2
                candidates = self.get_dst_candidates(mappings, t)
                best = None
                max_val = -1
                for cand in candidates:
                    sim = similarity_metrics.dice_similarity(t, cand, mappings)
                    if sim > max_val and sim >= self.sim_threshold: # line 3 alg 2
                        max_val = sim
                        best = cand
                        
                if best is not None:
                    self.last_chance_match(mappings, t, best)
                    mappings.add_mapping(t, best)
                    
        return mappings

class BobaVariableMatcher(GreedyBottomUpMatcher):
    DEFAULT_BOBA_VAR_HEIGHT_THRESHOLD = 2
    
    def __init__(self):
        self.boba_var_height_threshold = self.DEFAULT_BOBA_VAR_HEIGHT_THRESHOLD
        super().__init__()
        
    def configure(self, properties: Dict):
        self.boba_var_height_threshold = properties.get('boba_var_height_threshold', 
                                                        self.DEFAULT_BOBA_VAR_HEIGHT_THRESHOLD)
        super().configure(properties)
                
    def match(self, src: BobaTree, dst: BobaTree, mappings: MappingStore) -> MappingStore:
        for t in src.post_order(): # line 1 in alg 2
            if t.is_root():
                mappings.add_mapping(t, dst)
                self.last_chance_match(mappings, t, dst)
                break
            elif not(mappings.is_src_mapped(t) or t.is_leaf()): # t1 is not matched and t1 has children, line 1 in alg2
                candidates = self.get_dst_candidates(mappings, t)
                best = None
                max_val = -1
                for cand in candidates:
                    # if there is a boba variable in the children then let's loosen the threshold for matching
                    if t.has_boba_var(self.boba_var_height_threshold):
                        sim_threshold = self.sim_threshold - 0.2
                    else:
                        sim_threshold = self.sim_threshold    
                    sim = similarity_metrics.dice_similarity_offset(t, cand, mappings, t.num_child_boba_vars, t.num_child_boba_var_nodes)
                    if sim > max_val and sim >= sim_threshold: # line 3 alg 2
                        max_val = sim 
                        best = cand
                        
                if best is not None:
                    self.last_chance_match(mappings, t, best)
                    mappings.add_mapping(t, best)
        
        for t in src.post_order():
            if t.node_type == BOBA_VAR:
                candidates = self.get_boba_candidates(mappings, t)
            
        return mappings
    
    def get_dst_candidates(self, mappings: MappingStore, src: Tree) -> List[Tree]:
        """
        A node c ∈ T2 is a candidate for t1 if label(t1) = label(c), c is unmatched, and t1
        and c have some matching descendants.
        """
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
                if (src.node_type != BOBA_VAR) and (parent.node_type == src.node_type) and not(mappings.is_dst_mapped(parent) or parent.is_root()):
                    candidates.append(parent)
                seed = parent
        return candidates
    
    def get_boba_candidates(self, mappings: MappingStore, src: BobaTree):
        src_parents = src.get_parents() 
        map_list = [mappings.is_src_mapped(p) for p in src_parents]
        first_ind = map_list.index(True)
        dst_parent = mappings.get_dst_for_src(src_parents[first_ind])
        src_parent = src_parents[first_ind]
        dst_str = dst_parent.ast_code
        src_parent_str = src_parents[0].ast_code
        dst_mapped = [mappings.is_dst_mapped(p) for p in dst_parent.get_parents()]
        if all(map_list): # good boba mapping
            dst_children = dst_parent.children
            src_children = src_parents[first_ind].children
            
            src_child_pos = src_parent.get_child_position(src)
            if len(dst_children) == len(src_children):
                same_children = all((dst_children[ind].has_same_type_and_label(src_children[ind])) 
                                    for ind in range(len(src_children)) if ind != src_child_pos)
                if same_children:
                    dst = dst_parent.children[src_child_pos]
                    new_node = src.deep_copy()
                    new_node.metadata = dst.metadata
                    dst_parent.children.pop(src_child_pos)
                    dst_parent.insert_child(new_node, src_child_pos)
                    mappings.add_mapping(src, new_node)
                    mappings.add_boba_mapping(src, dst)
