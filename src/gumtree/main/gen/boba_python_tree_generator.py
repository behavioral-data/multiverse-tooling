from typing import Dict
from src.gumtree.main.gen.python_tree_generator import PythonTreeGenerator
from src.gumtree.main.trees.node_constants import BOBA_VAR
from src.gumtree.main.trees.boba_tree import BobaTree
from parso.tree import NodeOrLeaf

from src.boba.parser import History

from src.gumtree.main.trees.tree import Tree


def get_tree_hash(src_code) -> int:
    tree = PythonTreeGenerator().generate_tree(src_code).root.children[0] # root node is module level
    return tree.tree_metrics.structure_hash

def get_tree_size(src_code) -> int:
    tree = PythonTreeGenerator().generate_tree(src_code).root.children[0]
    return tree.tree_metrics.size

BOBA_VAR_EXAMPLE = "{{var_name}}"
BOBA_VAR_TREE_STRUCTURE_HASH = get_tree_hash(BOBA_VAR_EXAMPLE)

def is_boba_var(tree: Tree):
    return tree.tree_metrics.structure_hash == BOBA_VAR_TREE_STRUCTURE_HASH

def get_var_name(boba_var: str):
    return boba_var.strip()[2: -2]

class BobaPythonTemplateTreeGeneator(PythonTreeGenerator):
    
    def __init__(self, extra_data: Dict=None):
        if extra_data is not None and "parser_history" in extra_data:
            self.history: History = extra_data["parser_history"]
            self.boba_var_decs: Dict[str, str] = {dec_rec.parameter: dec_rec.option for dec_rec in self.history.decisions}
        else:
            self.history = None
            self.boba_var_decs = None
        
    def generate_tree_helper(self, ast_node: NodeOrLeaf) -> BobaTree:
        tree = super().generate_tree_helper(ast_node)
        if tree is None:
            return None
        if is_boba_var(tree):
            boba_var_name = get_var_name(ast_node.get_code())
            new_tree = BobaTree(BOBA_VAR, boba_var_name, ast_node.get_code())
            new_tree.pos = tree.pos
            new_tree.length = tree.length
            if self.boba_var_decs is not None:
                new_tree.num_boba_var_nodes = get_tree_size(self.boba_var_decs[boba_var_name])
            else:
                new_tree.num_boba_var_nodes = 0
        else:
            new_tree = BobaTree.deep_copy_from_other(tree)
            
        return new_tree
        