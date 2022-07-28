from abc import ABC, abstractmethod
from pickle import NONE
from typing import Dict, List, Tuple, Set
from src.gumtree.main.matchers.default_priority_tree_queue import DefaultPriorityTreeQueue, PythonPriorityTreeQueue
from src.gumtree.main.matchers.mapping_store import MappingStore
from src.gumtree.main.matchers.hash_based_mapper import HashBasedMapper
from src.gumtree.main.matchers.matcher import Matcher
from src.gumtree.main.trees.tree import Tree


class AbstractSubtreeMatcher(Matcher, ABC):
    DEFAULT_MIN_PRIORITY = 2
    DEFAULT_PRIORITY_CALCULATOR = "height"
    
    
    def __init__(self):
        self.min_priority = self.DEFAULT_MIN_PRIORITY
        self.src: Tree = None
        self.dst: Tree = None
        self.mappings: MappingStore = None
        self.PRIORITY_QUEUE_CLS = DefaultPriorityTreeQueue
        self.priority_calculator = self.PRIORITY_QUEUE_CLS.get_priority_calculator(self.DEFAULT_PRIORITY_CALCULATOR)

    def configure(self, properties: Dict):
        priority_queue_name = properties.get('priority_queue', "default")
        if priority_queue_name == "default":
            self.PRIORITY_QUEUE_CLS = DefaultPriorityTreeQueue
        elif priority_queue_name == "python":
            self.PRIORITY_QUEUE_CLS = PythonPriorityTreeQueue
        
        self.min_priority = properties.get('min_priority', self.DEFAULT_MIN_PRIORITY)
        self.priority_calculator = self.PRIORITY_QUEUE_CLS.get_priority_calculator(
            properties.get('priority_calculator', self.DEFAULT_PRIORITY_CALCULATOR))
        
    def match(self, src: Tree, dst: Tree, mappings: MappingStore=None) -> MappingStore:
        if mappings is None:
            mappings = MappingStore(src, dst)
        self.src = src
        self.dst = dst
        self.mappings = mappings # M in alg 1
        
        ambiguous_mappings: List[Tuple[Set[Tree], Set[Tree]]] = [] # A in alg 1
        
        src_trees = self.PRIORITY_QUEUE_CLS(src, self.min_priority, self.priority_calculator)
        dst_trees = self.PRIORITY_QUEUE_CLS(dst, self.min_priority, self.priority_calculator)
        
        
        while self.PRIORITY_QUEUE_CLS.synchronize(src_trees, dst_trees):
            local_hash_mappings = HashBasedMapper()
            local_hash_mappings.add_srcs(src_trees.pop())
            local_hash_mappings.add_dsts(dst_trees.pop())
            
            for pair in local_hash_mappings.unique(): # line 16 in alg 1
                any_src_tree = next(iter(pair[0])) # pair[0] should be length 1
                any_dst_tree = next(iter(pair[1])) # pair[1] should be length 1
                self.mappings.add_mapping_recursively(any_src_tree, any_dst_tree)
                
            for pair in local_hash_mappings.ambiguous(): # line 15 in alg 1
                ambiguous_mappings.append(pair)
                
            for pair in local_hash_mappings.unmapped():
                for tree in pair[0]: 
                    src_trees.open(tree) # line 18 in alg 1
                for tree in pair[1]:
                    dst_trees.open(tree)  # line 19 in alg 1
        
        self.handle_ambiguous_mappings(ambiguous_mappings) # line 20 - 25 in alg 1
        return self.mappings 
    
    @abstractmethod
    def handle_ambiguous_mappings(ambiguous_mappings: List[Tuple[Set[Tree], Set[Tree]]]):
        pass
    
    