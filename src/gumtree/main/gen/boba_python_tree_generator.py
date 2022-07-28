import ast
from typing import Dict
from src.ast_traverse import NodeVisitorStack
from src.gumtree.main.gen.python_tree_generator import PythonTreeGenerator
from src.gumtree.main.trees.node_constants import BOBA_VAR
from src.gumtree.main.trees.boba_tree import BobaTree

from src.boba.parser import History


def node_set_and_length_one(node: ast.AST) -> bool:
    return len(node.elts) == 1 and isinstance(node.elts[0], ast.Set)

def node_name_and_length_one(node: ast.AST) -> bool:
    return len(node.elts) == 1 and isinstance(node.elts[0], ast.Name)  

def is_boba_variable(node: ast.AST) -> bool:
    return isinstance(node, ast.Set) and node_set_and_length_one(node) and node_name_and_length_one(node.elts[0]) # {{boba_var}}


class BobaPythonTemplateTreeGeneator(PythonTreeGenerator):
    
    def __init__(self, extra_data: Dict):
        assert "parser_history" in extra_data, "need parser history for boba template tree generatation"
        self.history: History = extra_data["parser_history"]
        self.boba_var_decs: Dict[str, str] = {dec_rec.parameter: dec_rec.option for dec_rec in self.history.decisions}
        
        
    def generate_tree_helper(self, ast_node: ast.AST) -> BobaTree:
        if is_boba_variable(ast_node):
            raw_code = ast.unparse(ast_node)
            boba_var_name = raw_code[2: -2] #{{boba_var}} only get boba_var
            
            boba_var_node: ast.AST = ast.parse(self.boba_var_decs[boba_var_name])
            boba_var_node: BobaTree = self.generate_tree_helper(boba_var_node)
            
            node = BobaTree(BOBA_VAR, boba_var_name, ast.Constant(raw_code))
            node.metadata = self.get_metadata(ast_node)
            node.num_boba_var_nodes = boba_var_node.tree_metrics.size - 2 # minus one for module node and minus one for expr node
            return node
        else:
            node = BobaTree(self.get_node_type(ast_node), self.get_node_label(ast_node),
                            ast_node)
            node.metadata = self.get_metadata(ast_node)        
            children = NodeVisitorStack.get_children(ast_node)
            tree_children = [self.generate_tree_helper(child) for child in children]
            node.children = tree_children
            return node