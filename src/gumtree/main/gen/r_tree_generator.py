import ast
import os.path as osp
from typing import Dict, Union
import tree_sitter
from tree_sitter import Language, Parser

from src.gumtree.main.gen.tree_generator import TreeGenerator
from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.trees.tree_context import TreeContext
from src.gumtree.main.trees.boba_tree import TreeWMetaData

from src.utils import SRC_DIR
import yaml

TREE_SITTER_DIR = osp.join(SRC_DIR, 'gumtree', 'tree-sitter-parser')
BUILD_DIR = osp.join(TREE_SITTER_DIR, 'build-r', 'languages.so')
RULES_FILE = osp.join(TREE_SITTER_DIR, 'rules.yml')


Language.build_library(BUILD_DIR,
                       [osp.join(TREE_SITTER_DIR, 'tree-sitter-r')]
)
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


class RTreeGenerator(TreeGenerator):
	def generate_tree(self, src_code: str, metadata=None) -> TreeContext:
		self.positions = get_positions(src_code)
		self.code_str = src_code
		parser = Parser()
		parser.set_language(Language(osp.join(BUILD_DIR), 'r'))
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


if __name__ == "__main__":
    gen = RTreeGenerator()
    f = '[redacted_for_anonymity]/MultiverseProject/MultiverseTooling/multiverse-tooling/data/hurricane/template.R'
    t = gen.generate_tree_from_file(f)
    t.root.viz_graph()
    print('here')