
from typing import Dict
from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.matchers.matcher import Matcher
from src.gumtree.main.trees.tree_context import TreeContext
from src.gumtree.main.matchers.mapping_store import MappingStore
from src.gumtree.main.diff.edit_script import EditScript
from src.gumtree.main.gen.tree_generators import TreeGeneratorFactory
from src.gumtree.main.matchers.composite_matchers import MatcherFactory
from src.gumtree.main.diff.chawathe_script_generator import ChawatheScriptGenerator

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
    
    @classmethod
    def compute_from_strs(cls, src_code, dst_code, tree_generator_name: str,
                matcher_name: str, configurations: Dict=None):
        tree_generator = TreeGeneratorFactory(tree_generator_name).get_generator()
        src = tree_generator.generate_tree(src_code)
        dst = tree_generator.generate_tree(dst_code)
        
        matcher = MatcherFactory(matcher_name).get_matcher()
        matcher.configure(configurations)
        mappings = matcher.match(src.root, dst.root, MappingStore(src.root, dst.root))
        edit_script = ChawatheScriptGenerator.compute_actions(mappings)
        return cls(src, dst, mappings, edit_script)