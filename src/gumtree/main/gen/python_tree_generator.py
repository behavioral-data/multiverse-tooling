import ast
from typing import Union
import parso
from parso.tree import NodeOrLeaf

from src.gumtree.main.gen.tree_generator import TreeGenerator
from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.trees.tree_context import TreeContext
from src.gumtree.main.trees.boba_tree import PythonTree

def get_positions(src_code):
	positions = [0]
	index = 0
	for c in src_code:
		index += 1
		if c == '\n':
			positions.append(index)
	return positions

class PythonTreeGenerator(TreeGenerator):
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
		ast_node = ast.parse(src_code)
		tree = self.generate_tree_helper(ast_node)
		tree_ctx = TreeContext()
		tree_ctx.root = tree
		
		if metadata is not None and type(metadata) is dict:
			for k, v in metadata.items():
				tree_ctx.set_metadata(k, v)
		return tree_ctx
	
	
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
		node = PythonTree(ast_node.type, label, ast_code=ast_node.get_code())
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