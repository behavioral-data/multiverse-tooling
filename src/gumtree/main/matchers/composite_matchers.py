

from typing import List

from src.gumtree.main.matchers.matcher import Matcher
from src.gumtree.main.matchers.greedy_bottomup_matcher import GreedyBottomUpMatcher
from src.gumtree.main.matchers.greedy_subtree_matcher import GreedySubtreeMatcher

from src.gumtree.main.matchers.mapping_store import MappingStore
from src.gumtree.main.trees.tree import Tree

class CompositeMatcher(Matcher):
    def __init__(self, matchers: List[Matcher]):
        self.matchers = matchers
        
    def match(self, src: Tree, dst: Tree, mappings: MappingStore):
        for matcher in self.matchers:
            mappings = matcher.match(src, dst, mappings)
        return mappings
    
    def configure(self, configurations):
        for matcher in self.matchers:
            matcher.configure(configurations)
        
        
class ClassicGumTree(CompositeMatcher):
    def __init__(self):
        super().__init__([GreedySubtreeMatcher(), GreedyBottomUpMatcher()])