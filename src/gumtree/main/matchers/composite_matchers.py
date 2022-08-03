

from typing import List

from src.gumtree.main.matchers.matcher import Matcher
from src.gumtree.main.matchers.greedy_bottomup_matcher import GreedyBottomUpMatcher, BobaVariableMatcher
from src.gumtree.main.matchers.greedy_subtree_matcher import GreedySubtreeMatcher

from src.gumtree.main.matchers.mapping_store import MappingStore
from src.gumtree.main.trees.tree import Tree
from src.boba.codeparser import BlockCode

from src.gumtree.main.matchers.boba_template_intermediary_matcher import BobaTemplateIntermediaryMatcher

class MatcherFactory:
    def __init__(self, matcher_name: str):
        self.matcher_name = matcher_name
        
    def get_matcher(self):
        if self.matcher_name == "classic":
            return ClassicGumTree()
        elif self.matcher_name == "boba":
            return BobaVariableGumTree()
        else:
            raise NotImplementedError(f"Matcher {self.matcher_name} not implemented")

class CompositeMatcher(Matcher):
    def __init__(self, matchers: List[Matcher]):
        self.matchers = matchers
        
    def match(self, src: Tree, dst: Tree, mappings: MappingStore=None):
        if mappings is None:
            mappings = MappingStore(src, dst)
        for matcher in self.matchers:
            mappings = matcher.match(src, dst, mappings)
        return mappings
    
    def configure(self, configurations):
        if configurations is None:
            configurations = {}
        for matcher in self.matchers:
            matcher.configure(configurations)
        
        
class ClassicGumTree(CompositeMatcher):
    def __init__(self):
        super().__init__([GreedySubtreeMatcher(), GreedyBottomUpMatcher()])
        
class BobaVariableGumTree(CompositeMatcher):
    def __init__(self):
        super().__init__([GreedySubtreeMatcher(), BobaVariableMatcher()])

class BobaTemplateMatcher(CompositeMatcher):
    def __init__(self, 
                 src_code_blocks: List[BlockCode],
                 dst_code_blocks: List[BlockCode]):
        super().__init__([BobaTemplateIntermediaryMatcher(src_code_blocks, dst_code_blocks),
                          GreedyBottomUpMatcher()])
