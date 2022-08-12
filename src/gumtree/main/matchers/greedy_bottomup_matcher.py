from src.gumtree.main.matchers.abstract_bottom_up_matcher import AbstractBottomUpMatcher
from src.gumtree.main.matchers.mapping_store import MappingStore
import src.gumtree.main.matchers.similarity_metrics as similarity_metrics
from src.gumtree.main.trees.tree import Tree

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