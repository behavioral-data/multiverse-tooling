
from typing import Dict, Union, Tuple
from src.gumtree.main.trees.tree_context import TreeContext
from src.gumtree.main.matchers.mapping_store import MappingStore
from src.gumtree.main.diff.edit_script import EditScript
from src.gumtree.main.gen.tree_generators import TreeGeneratorFactory
from src.gumtree.main.matchers.composite_matchers import MatcherFactory
from src.gumtree.main.diff.chawathe_script_generator import ChawatheScriptGenerator

from src.gumtree.main.diff.actions.tree_classifier import (
    AllNodesClassifier,
    OnlyRootsClassifier,
    TreeClassifier,
)


class Diff:
    def __init__(self, src: TreeContext, dst: TreeContext, 
                 mappings: MappingStore, edit_script: EditScript):
        self.src = src
        self.dst = dst
        self.mappings = mappings
        self.edit_script = edit_script
    
    @classmethod
    def compute(cls, src_file, dst_file, tree_generator_name: str,
                matcher_name: str, configurations: Dict=None):
        tree_generator = TreeGeneratorFactory(tree_generator_name).get_generator()
        src = tree_generator.generate_tree_from_file(src_file)
        dst = tree_generator.generate_tree_from_file(dst_file)
        
        matcher = MatcherFactory(matcher_name).get_matcher()
        matcher.configure(configurations)
        mappings = matcher.match(src.root, dst.root, MappingStore(src.root, dst.root))
        edit_script = ChawatheScriptGenerator().compute_actions(mappings)
        return cls(src, dst, mappings, edit_script)
    
    @staticmethod
    def get_src_dst_trees(src_code, dst_code, tree_generator_name: Union[str, Tuple[str, str]],
                          configurations) -> Tuple[TreeContext, TreeContext]:
        if type(tree_generator_name) is str:
            tree_generator = TreeGeneratorFactory(tree_generator_name, configurations).get_generator()
            src = tree_generator.generate_tree(src_code)
            dst = tree_generator.generate_tree(dst_code)
        else:
            tree_generator_src = TreeGeneratorFactory(tree_generator_name[0], configurations).get_generator()
            tree_generator_dst = TreeGeneratorFactory(tree_generator_name[1], configurations).get_generator()
            src = tree_generator_src.generate_tree(src_code)
            dst = tree_generator_dst.generate_tree(dst_code)
        
        return src, dst
    
    @classmethod
    def compute_from_strs(cls, src_code, dst_code, tree_generator_name: Union[str, Tuple[str, str]],
                matcher_name: str, configurations: Dict=None):
        src, dst = cls.get_src_dst_trees(src_code, dst_code, tree_generator_name, configurations)
        matcher = MatcherFactory(matcher_name).get_matcher()
        matcher.configure(configurations)
        mappings = matcher.match(src.root, dst.root, MappingStore(src.root, dst.root))
        edit_script = ChawatheScriptGenerator.compute_actions(mappings)
        return cls(src, dst, mappings, edit_script)
    
    def createAllNodeClassifier(self) -> TreeClassifier:
        return AllNodesClassifier(self)
    
    def createRootNodesClassifier(self) -> TreeClassifier:
        return OnlyRootsClassifier(self)