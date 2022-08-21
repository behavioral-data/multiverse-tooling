from collections import defaultdict
from copy import deepcopy
import json
from typing import Dict, List, Tuple

from src.boba.parser import History, Parser
from src.boba.codeparser import BlockCode
from src.gumtree.main.diff.diff import Diff
from src.gumtree.main.client.line_diff import LineDiff, LinePosMark

from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.client.template_builder import BlockInfo, CodePos, NewTemplateBuilder

from src.utils import OUTPUT_DIR
from src.gumtree.main.client.boba_utils import chunk_code_from_pos, clean_code_blocks, get_tree, parse_boba_var_config_ast, get_universe_blocks_from_template_blocks
from src.gumtree.main.diff.chawathe_script_generator import ChawatheScriptGenerator

from src.gumtree.main.gen.python_tree_generator import PythonParsoTreeGenerator
from src.gumtree.main.matchers.composite_matchers import MatcherFactory
from src.gumtree.main.trees.tree_context import TreeContext

from src.gumtree.main.matchers.mapping_store import MappingStore

from src.gumtree.main.trees.tree_chunk import MappedBobaVar, OffsetsFromBobaVar, get_tree_chunks, get_tree_chunks_from_blocks, get_tree_chunks_from_mapping


PYTHON_CONFIGURATIONS = {
	"generator": "python",
	"matcher": "classic",
	"min_priority": 0,
	"priority_queue": "python"
}

R_CONFIGURATIONS = {
	"generator": "r",
	"matcher": "classic",
	"min_priority": 0,
	"priority_queue": "r"
}


class TemplateDiff(LineDiff):
	def __init__(self, ps: Parser, universe_code: str, universe_num: int):
		
		self.boba_parser = ps
		self.universe_num = universe_num
		self.history: History = ps.history[universe_num - 1]
		intermediary_code = self.boba_parser.paths_code[self.history.path]
		u_code = deepcopy(intermediary_code)
		decision_dict = self.history.decision_dict
		decision_dict['_n'] = (str(universe_num), -1)
		for dec, (option, choice_ind) in self.history.decision_dict.items():
			dec_str = '{{' + dec + '}}'
			if option == '':
				intermediary_code = intermediary_code.replace(dec_str, '')
			u_code = u_code.replace(dec_str, option)
		u_code = u_code.replace('{{_n}}', str(universe_num))
		if self.boba_parser.lang.lang[0] == "python":
			configurations = PYTHON_CONFIGURATIONS
		else:
			configurations = R_CONFIGURATIONS
		configurations["parser_history"] = self.history
		
		super().__init__(u_code, universe_code, configurations)
		self.diff: Diff = self.get_diff()
		blocks = get_universe_blocks_from_template_blocks(self.boba_parser.code_parser.blocks,
														  self.boba_parser.blocks_code[self.universe_num - 1])
		self.tc = get_tree_chunks_from_blocks(self.diff.src.root, 
										 blocks,
										 decision_dict)
		mapped_boba_vars, unmapped = get_tree_chunks_from_mapping(self.diff.mappings, self.tc)
		# mapped_boba_vars = [mbv for mbv in mapped_vars if not mbv.boba_var.startswith('_')]
		self.new_intermediary_code, self.new_boba_var_pos = chunk_code_from_pos(self.dst_code, [('{{' + mapped_var.boba_var + '}}', mapped_var) for mapped_var in mapped_boba_vars])
		self.mapped_boba_vars = mapped_boba_vars
		self.old_u_t_diff = OffsetsFromBobaVar.init_from_tree_chunks(self.tc)
		self.new_u_t_diff = OffsetsFromBobaVar.init_from_mapped_vars(self.dst_code, mapped_boba_vars)
		
		u_code_blocks: List[BlockCode] = clean_code_blocks(self.boba_parser.blocks_code[self.universe_num - 1])
		template_code_blocks: List[BlockCode] = clean_code_blocks(self.boba_parser.code_parser.all_blocks)
		self.template_code = self.boba_parser.template_code
		self.template_code_pos = CodePos(u_code,
										 self.template_code,
										 BlockInfo(u_code_blocks),
										 BlockInfo(template_code_blocks)
										 )
		
		self.template_code_lines = self.template_code.split('\n')

	   
		self.classifier = self.diff.createRootNodesClassifier()
		
		
		# generate new boba spec (need diff)
		self.template_config_tree = get_tree(self.boba_parser.code_parser.raw_spec)
		self.boba_var_to_tree_options = parse_boba_var_config_ast(self.template_config_tree)
		self.var_tree_mappings, self.template_spec_tree_to_boba_choice_var = self.handle_boba_vars(self.dst_code, [mbv for mbv in mapped_boba_vars if not mbv.boba_var.startswith('_')])
		self.new_raw_spec, _ = chunk_code_from_pos(self.boba_parser.code_parser.raw_spec, self.var_tree_mappings)
		self.old_raw_spec = self.boba_parser.code_parser.raw_spec
		self.spec_diff = self.get_spec_diff()
		self.spec_classifier = self.spec_diff.createRootNodesClassifier()
		self.template_builder = NewTemplateBuilder(self.template_code_pos,
												   self.new_intermediary_code,
												   self.new_raw_spec)
		self.template_builder_instaniated = NewTemplateBuilder(self.template_code_pos,
															  universe_code,
															  self.new_raw_spec)
		
		self.new_template_i_code_pos = self.template_builder.new_template_code_pos
		self.new_template_u_code_pos = CodePos(universe_code,
											   self.template_builder.new_template_code_pos.template_code_str,
											   self.template_builder_instaniated.new_template_code_pos.u_block_info,
											   self.template_builder.new_template_code_pos.template_block_info
											 )
		
		
	def get_spec_diff(self):
		src = TreeContext()
		src.root = self.template_config_tree
		src.root.parent = None
		dst = PythonParsoTreeGenerator().generate_tree(self.new_raw_spec)
		matcher = MatcherFactory("classic").get_matcher()
		matcher.configure({"priority_queue": "default", "min_priority": 0})

		mappings = matcher.match(src.root, dst.root,  MappingStore(src.root, dst.root))
		edit_script = ChawatheScriptGenerator.compute_actions(mappings)
		return Diff(src, dst, mappings, edit_script)
	

	def handle_boba_vars(self, code_str, mapped_boba_vars: List[MappedBobaVar]) -> List[Tuple[str, Tree]]:
		boba_var_to_mapped_tree: Dict[str] = defaultdict(set)
		for mbv in mapped_boba_vars:
			boba_var_to_mapped_tree[mbv.boba_var].add(mbv.get_str(code_str))

		mappings: List[Tuple[str, Tree]] = [] 
		tree_to_boba_choice_var = {}
		for k, v in boba_var_to_mapped_tree.items():
			if len(v) > 1:
				print(f'Multiple values for same boba var: {k}\n{v}')
			choice_idx = self.history.decision_dict[k][1]
			v_tree = self.boba_var_to_tree_options[k][choice_idx]
			replace_v = list(v)[0]
			if self.boba_parser.lang.lang[0] == "python":
				try:
					var_unchanged = eval(str(json.loads(v_tree.ast_code))) == eval(replace_v)
				except Exception as e:
					var_unchanged = str(json.loads(v_tree.ast_code)) == replace_v
			else:
				var_unchanged = str(json.loads(v_tree.ast_code)) == replace_v
			if var_unchanged:
				continue
			try:
				json.loads(replace_v)
				s = replace_v
			except json.decoder.JSONDecodeError:
				s = json.dumps(replace_v)
			finally:
				mappings.append((s,  v_tree))
				tree_to_boba_choice_var[v_tree] = k
		return mappings, tree_to_boba_choice_var

	
	def run(self):        
		"""
		We generate the tempalte based on line diffs and offsets
		We gather the block boundaries for uprime based on line diff between uprime and i
		We then use this to insert into the template file when the block correpsonds to uprime
		This gives us a generated t prime.
		
		We then calcualte the position of the edits by adding line offsets 
		between the start of blocks in uprime and the start of blocks in tprime.
		
		We do something similar for i and t
		
		"""
		new_template_code = self.template_builder.new_template_code_pos.template_code_str
		src_str_lines, dst_str_lines = self.produce(self.template_code_lines, 
													new_template_code.split('\n'), 
													)
		
		self.write_code(src_str_lines, 
						dst_str_lines, 
						self.template_code, 
						new_template_code)
		
		self.write_to_file(osp.join(OUTPUT_DIR, 'template.py'), 
						   osp.join(OUTPUT_DIR, 'template_changed.py'),
						   self.template_code, new_template_code) 
		

	# def get_line_marks(self, 
	# 				   src_code_lines: List[str],
	# 				   dst_code_lines: List[str]) -> Tuple[Dict[int, List[LinePosMark]],
	# 													   Dict[int, List[LinePosMark]]]:
	# 	src_line_to_mark: Dict[int, List[LinePosMark]] = defaultdict(list)
	# 	dst_line_to_mark: Dict[int, List[LinePosMark]] = defaultdict(list)
		
	# 	self._get_line_marks_helper(src_code_lines,
	# 							   dst_code_lines,
	# 							   self.spec_diff,
	# 							   self.spec_classifier,
	# 							   get_pos_src=self.template_code_pos.get_template_boba_conf_pos_from_u,
	# 							   get_pos_dst=self.template_builder.new_template_code_pos.get_template_boba_conf_pos_from_u,
	# 							   src_line_to_mark=src_line_to_mark,
	# 							   dst_line_to_mark=dst_line_to_mark
	# 							   ) 
		
	# 	for t in self.diff.src.root.pre_order():
	# 		pos = self.template_code_pos.get_template_pos_from_u(t)
	# 		if t in self.classifier.get_updated_srcs():
	# 			self.add_line_mark(pos, src_code_lines, src_line_to_mark, self.UPDATE_TAG)
	# 		if t in self.classifier.get_deleted_srcs():
	# 			self.add_line_mark(pos, src_code_lines, src_line_to_mark, self.DEL_TAG)

	# 	for t in self.diff.dst.root.pre_order():
	# 		pos = self.template_builder.new_template_code_pos.get_template_pos_from_u(i_t)
	# 		if t in self.classifier.get_updated_dsts():
	# 			self.add_line_mark(pos, dst_code_lines, dst_line_to_mark, self.UPDATE_TAG)
	# 		if t in self.classifier.get_inserted_dsts():
	# 			self.add_line_mark(pos, dst_code_lines, dst_line_to_mark, self.INSERT_TAG)
	# 	# go through positions in changed dicionary  
	# 	return src_line_to_mark, dst_line_to_mark
	
	# def write_to_file(self, f1, f2, t, t_prime):
	# 	with open(f1, 'w') as f:
	# 		f.write(t)
	# 	with open(f2, 'w') as f:
	# 		f.write(t_prime)
	# 	print(f'saved to {f1}')
	# 	print(f'saved to {f2}')
		
		
		
if __name__ == "__main__":
	from src.utils import load_parser_example
	
	from src.utils import load_parser_example, read_universe_file, DATA_DIR
	import os.path as osp

	dataset, ext = 'hurricane', 'R'
	save_file = osp.join(DATA_DIR, f'{dataset}_template_parser_obj_0804.pickle')
	
	# ps = Parser('/projects/bdata/kenqgu/Research/MultiverseProject/MultiverseTooling/multiverse-tooling/data/hurricane/template.R', 
    #          	'.', None)
	# ps.main()
	ps = load_parser_example(dataset, ext, None, run_parser_main=True)
	# # ps._parse_blocks()
	universe_num = 3
	universe_code = read_universe_file(universe_num, dataset, ext)
	line_diff = TemplateDiff(ps, universe_code, universe_num)
	# res = line_diff.run()s