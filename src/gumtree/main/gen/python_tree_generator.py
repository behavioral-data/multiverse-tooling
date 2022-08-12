import ast
from typing import Dict, Union
import parso
from parso.tree import NodeOrLeaf

from src.gumtree.main.gen.tree_generator import TreeGenerator
from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.trees.tree_context import TreeContext
from src.gumtree.main.trees.boba_tree import TreeWMetaData
import tree_sitter
from tree_sitter import Language, Parser
import os.path as osp

from src.gumtree.main.gen.tree_generator import TreeGenerator
from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.trees.tree_context import TreeContext
from src.gumtree.main.trees.boba_tree import TreeWMetaData

from src.utils import SRC_DIR
import yaml

TREE_SITTER_DIR = osp.join(SRC_DIR, 'gumtree', 'tree-sitter-parser')
BUILD_DIR = osp.join(TREE_SITTER_DIR, 'build-python', 'languages.so')
RULES_FILE = osp.join(TREE_SITTER_DIR, 'rules.yml')



EMPTY_CONFIG = {'flattened': ["string"], 'aliased': {}, 'ignored': []}
with open(RULES_FILE, "r") as stream:
  TREE_REWRITE_RULES = yaml.safe_load(stream)
  
  
def get_positions(src_code):
	positions = [0]
	index = 0
	for c in src_code:
		index += 1
		if c == '\n':
			positions.append(index)
	return positions


class PythonTreeGenerator(TreeGenerator):
	def generate_tree(self, src_code: str, metadata=None) -> TreeContext:
		self.positions = get_positions(src_code)
		self.code_str = src_code
		parser = Parser()
		Language.build_library(BUILD_DIR,
                       [osp.join(TREE_SITTER_DIR, 'tree-sitter-python')]
		)
		parser.set_language(Language(osp.join(BUILD_DIR), 'python'))
		config = EMPTY_CONFIG
		tree = parser.parse(bytes(src_code, "utf8")).root_node
		tree = self.generate_tree_helper(tree, config)
		tree_ctx = TreeContext()
		tree_ctx.root = tree
		
		if metadata is not None and type(metadata) is dict:
			for k, v in metadata.items():
				tree_ctx.set_metadata(k, v)
		return tree_ctx
		
	def generate_tree_helper(self, ts_node: tree_sitter.Tree, config: Dict) -> Union[Tree, None]:
		node_type = config['aliased'][ts_node.type] if ts_node.type in config['aliased'] else ts_node.type
		start_pos = self.positions[ts_node.start_point[0]] + ts_node.start_point[1]
		end_pos = self.positions[ts_node.end_point[0]] + ts_node.end_point[1]
		length = end_pos - start_pos
		if ts_node.child_count == 0 or ts_node.type in config['flattened']:
			label = ts_node.text.decode('utf8')
		else:
			label = ""
		node = TreeWMetaData(node_type, label, ast_code=ts_node.text.decode('utf8'))
		node.pos = start_pos
		node.length = length
		
		node.metadata = {
			"lineno": ts_node.start_point[0] + 1,
	   		"col_offset": ts_node.start_point[1],
			"end_lineno": ts_node.end_point[0] + 1,
			"end_col_offset": ts_node.end_point[1]
		}
  
		tree_children = []
		if not ts_node.type in config['flattened']:
			for child in ts_node.children:
				if not ts_node.type in config['ignored']:
					child_node = self.generate_tree_helper(child, config)
					tree_children.append(child_node)
		node.children = tree_children
		return node


class PythonParsoTreeGenerator(TreeGenerator):
	@staticmethod
	def get_node_label(node: ast.AST):
		labels = []
		skip_fields = ["lineno", "col_offset", "end_lineno", "end_col_offset"]
		for field, value in list(ast.iter_fields(node)):
			if (type(value) is int or type(value) is str) and field not in skip_fields:
				labels.append(f"{field}={value}")
		return ", ".join(labels)
	
	@staticmethod
	def get_metadata(node: ast.AST):
		ret = {}
		for field in ["lineno", "col_offset", "end_lineno", "end_col_offset"]:
			if hasattr(node, field):
				ret[field] = getattr(node, field)
		return ret
	
	@staticmethod
	def get_node_type(node: ast.AST):
		return node.__class__.__name__
	
	def generate_tree(self, src_code: str, metadata=None) -> TreeContext:
		self.positions = get_positions(src_code)
		self.code_str = src_code
		parso_ast: NodeOrLeaf = parso.parse(src_code)
		tree = self.generate_tree_helper(parso_ast)
		tree_ctx = TreeContext()
		tree_ctx.root = tree
		
		if metadata is not None and type(metadata) is dict:
			for k, v in metadata.items():
				tree_ctx.set_metadata(k, v)
		return tree_ctx
		
	def generate_tree_helper(self, ast_node: NodeOrLeaf) -> Union[Tree, None]:
		if ast_node.type in ['keyword', 'newline', 'endmarker']:
			return None
		if ast_node.type == 'operator' and ast_node.value in ['.', '(', ')', '[', ']', ':', ';']:
			return None
		
		if (not hasattr(ast_node, 'children')) or len(ast_node.children) == 0:
			label = ast_node.value
		else:
			label = ""
		
		start_pos = self.positions[ast_node.start_pos[0] - 1] + ast_node.start_pos[1]
		end_pos = self.positions[ast_node.end_pos[0] - 1] + ast_node.end_pos[1]
		length = end_pos - start_pos
		node = TreeWMetaData(ast_node.type, label, ast_code=ast_node.get_code())
		node.pos = start_pos
		node.length = length
		
		node.metadata = {
			"lineno": ast_node.start_pos[0],
       		"col_offset": ast_node.start_pos[1],
            "end_lineno": ast_node.end_pos[0],
            "end_col_offset": ast_node.end_pos[1]
		}
  
		tree_children = []
		if hasattr(ast_node, "children"):
			for child in ast_node.children:
				child_node = self.generate_tree_helper(child)
				if child_node is not None:
					tree_children.append(child_node)
		node.children = tree_children
		return node

if __name__ == "__main__":
    from src.utils import VIZ_DIR
    import os.path as osp
    gen = PythonTreeGenerator()
    print('here')