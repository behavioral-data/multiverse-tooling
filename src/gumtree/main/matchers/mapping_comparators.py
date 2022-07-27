from collections import defaultdict
from typing import Dict, Set, List, Tuple
import math
from src.gumtree.main.matchers.mapping_store import MappingStore
import src.gumtree.main.matchers.similarity_metrics as similarity_metrics
import src.gumtree.main.sequence_algorithms as sequence_algorithms
from src.gumtree.main.trees.tree import Tree


Mapping = Tuple[Tree, Tree]

def compare(d1, d2):
    if d1 < d2:
        return -1
    if d1 > d2:
        return 1
    return 0


def cmp_to_key(mycmp):
    """
    From [Sorting HOW TO — Python 3.10.5 documentation](https://docs.python.org/3/howto/sorting.html)
    """
    'Convert a cmp= function into a key= function'
    class K:
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K
        

class FullMappingComparator:
    def __init__(self, ms: MappingStore) -> None:
        self.siblings_comparator = SiblingsSimilarityMappingComparator(ms)
        self.parents_comparator = ParentsSimilarityMappingComparator()
        self.parents_position_comparator = PositionInParentsSimilarityMappingComparator()
        self.position_comparator = AbsolutePositionDistanceMappingComparator()
            
    def compare(self, m1: Mapping, m2: Mapping):
        result = self.siblings_comparator.compare(m1, m2)  # line 20 alg 1
        if result != 0:
            return result

        result = self.parents_comparator.compare(m1, m2)
        if result != 0:
            return result
        
        result = self.parents_position_comparator.compare(m1, m2)
        if result != 0:
            return result
        
        return self.position_comparator.compare(m1, m2)
        
    
    
class SiblingsSimilarityMappingComparator:
    def __init__(self, ms: MappingStore) -> None:
        self.src_descendents: Dict[Tree, Set[Tree]] = defaultdict(set)
        self.dst_descendents: Dict[Tree, Set[Tree]] = defaultdict(set)
        self.cached_similarities: Dict[Mapping, float] = {}
        self.ms = ms
    
    def compare(self, m1: Mapping, m2: Mapping) -> int:
        if m1[0].parent == m2[0].parent and m1[1].parent == m2[1].parent:
            return 0
        
        if m1 not in self.cached_similarities:
            self.cached_similarities[m1] = similarity_metrics.dice_coefficient(
                self.common_descendents_nb(m1[0].parent, m1[1].parent),
                len(self.src_descendents.get(m1[0].parent, set())),
                len(self.dst_descendents.get(m1[1].parent, set()))
            )
            
        if m2 not in self.cached_similarities:
            self.cached_similarities[m2] = similarity_metrics.dice_coefficient(
                self.common_descendents_nb(m2[0].parent, m2[1].parent),
                len(self.src_descendents.get(m2[0].parent, set())),
                len(self.dst_descendents.get(m2[1].parent, set()))
            )
        
        # m2, m1 reversed because we want higher similarities first when sorted
        return compare(self.cached_similarities[m2], self.cached_similarities[m1])
        
    def common_descendents_nb(self, src: Tree, dst: Tree):
        for dsc in src.get_descendents():
            self.src_descendents[src].add(dsc)
        for dsc in dst.get_descendents():
            self.dst_descendents[dst].add(dsc)
        common = 0
        for t in self.src_descendents[src]:
            m = self.ms.get_dst_for_src(t)
            if m is not None and m in self.dst_descendents.get(dst, set()):
                common += 1
        return common
    
        
class ParentsSimilarityMappingComparator:
    def __init__(self):
        self.src_ancestors: Dict[Tree, List[Tree]] = {}
        self.dst_ancestors: Dict[Tree, List[Tree]] = {}
        self.cached_similarities: Dict[Mapping, float] = {}
        
    def compare(self, m1: Mapping, m2: Mapping) -> int:
        if m1[0].parent == m2[0].parent and m1[1].parent == m2[1].parent:
            return 0
        
        if m1[0] not in self.src_ancestors:
            self.src_ancestors[m1[0]] = m1[0].get_parents()
        if m1[1] not in self.dst_ancestors:
            self.dst_ancestors[m1[1]] = m1[1].get_parents()
        if m2[0] not in self.src_ancestors:
            self.src_ancestors[m2[0]] = m2[0].get_parents()
        if m2[1] not in self.dst_ancestors:
            self.dst_ancestors[m2[1]] = m2[1].get_parents()
            
        if m1 not in self.cached_similarities:
            self.cached_similarities[m1] = similarity_metrics.dice_coefficient(
                self.compare_parents_nb(m1[0], m1[1]),
                len(self.src_ancestors.get(m1[0], list())),
                len(self.dst_ancestors.get(m1[1], list()))
            )
            
        if m2 not in self.cached_similarities:
            self.cached_similarities[m2] = similarity_metrics.dice_coefficient(
                self.compare_parents_nb(m2[0], m2[1]),
                len(self.src_ancestors.get(m2[0], list())),
                len(self.dst_ancestors.get(m2[1], list()))
            )
        return compare(self.cached_similarities[m2], self.cached_similarities[m1])
        
    def compare_parents_nb(self, src: Tree, dst: Tree):
        return len(sequence_algorithms.longest_common_subsequence_with_type(
            self.src_ancestors[src],
            self.dst_ancestors[dst]
        ))
        
        
class PositionInParentsSimilarityMappingComparator:
    def compare(self, m1: Mapping, m2: Mapping) -> int:
        m1_distance = self.distance(m1)
        m2_distance = self.distance(m2)
        return compare(m1_distance, m2_distance)
    
    def distance(self, m: Mapping):
        pos_vector1 = self.pos_vector(m[0])
        pos_vector2 = self.pos_vector(m[1])
        ret_sum = 0
        for i in range(min(len(pos_vector1), len(pos_vector2))):
            ret_sum += (pos_vector1[i] - pos_vector2[i]) * (pos_vector1[i] - pos_vector2[i])
        return math.sqrt(ret_sum)
    
    def pos_vector(self, src: Tree):
        posvector = []
        current = src
        while current is not None and current.parent is not None:
            parent = current.parent
            pos = parent.get_child_position(current)
            posvector.append(pos)
            current = parent
        return posvector

class TextualPositionDistanceMappingComparator:
    pass

class AbsolutePositionDistanceMappingComparator:
    def compare(self, m1: Mapping, m2: Mapping) -> int:
        m1_pos_dist = self.absolute_position_difference(m1[0], m1[1])
        m2_pos_dist = self.absolute_position_difference(m2[0], m2[1])
        return compare(m1_pos_dist, m2_pos_dist)
    
    def absolute_position_difference(self, src: Tree, dst: Tree) -> int:
        return abs(src.tree_metrics.position - dst.tree_metrics.position)