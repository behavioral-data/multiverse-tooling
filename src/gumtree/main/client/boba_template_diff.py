import bisect
from collections import defaultdict
from functools import partial
import json
from typing import Dict, List, Tuple

from src.boba.parser import History, Parser
from src.boba.codeparser import BlockCode
from src.gumtree.main.diff.diff import Diff
from src.gumtree.main.client.line_diff import LineDiff, LinePosMark

from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.client.template_builder import BlockInfo, CodePos, NewTemplateBuilder

from src.utils import OUTPUT_DIR
from src.gumtree.main.client.boba_utils import chunk_code, clean_code_blocks, get_tree, parse_boba_var_config_ast
from src.gumtree.main.diff.chawathe_script_generator import ChawatheScriptGenerator

from src.gumtree.main.gen.python_tree_generator import PythonTreeGenerator
from src.gumtree.main.matchers.composite_matchers import MatcherFactory
from src.gumtree.main.trees.tree_context import TreeContext

from src.gumtree.main.matchers.mapping_store import MappingStore


PYTHON_CONFIGURATIONS = {
    "generator": ("boba_python_template", "python"),
    "matcher": "boba",
    "min_priority": 0,
    "priority_queue": "default"
}

R_CONFIGURATIONS = {
    "generator": ("boba_r_template", "r"),
    "matcher": "boba",
    "min_priority": 0,
    "priority_queue": "default"
}


class TemplateDiff(LineDiff):
    DEFAULT_GENERATOR = ("boba_python_template", "python")
    MATCHER =  "boba"
    PRIOIRITY_QUEUE = "python"

    def __init__(self, ps: Parser, universe_code: str, universe_num: int):
        
        self.boba_parser = ps
        self.universe_num = universe_num
        self.history: History = ps.history[universe_num - 1]
        intermediary_code = self.boba_parser.paths_code[self.history.path]
        if self.boba_parser.lang.lang[0] == "python":
            configurations = PYTHON_CONFIGURATIONS
        else:
            configurations = R_CONFIGURATIONS
        configurations["parser_history"] = self.history
        super().__init__(intermediary_code, universe_code, configurations)
        
        intermediary_code_blocks: List[BlockCode] = clean_code_blocks(self.boba_parser.blocks_code[self.universe_num - 1])
        template_code_blocks: List[BlockCode] = clean_code_blocks(self.boba_parser.code_parser.all_blocks)
        self.template_code = self.boba_parser.template_code
        self.template_code_pos = CodePos(intermediary_code,
                                         self.template_code,
                                         BlockInfo(intermediary_code_blocks),
                                         BlockInfo(template_code_blocks)
                                         )
        
        self.template_code_lines = self.template_code.split('\n')

        self.diff: Diff = self.get_diff()
        self.classifier = self.diff.createRootNodesClassifier()
        
        # generate intermediary code (need diff)
        self.new_intermediary_code = chunk_code(self.dst_code, 
                                                [('{{' + t.label + '}}', v) 
                                                 for t, v in self.diff.mappings.src_to_dst_boba_map.items()])
        self.new_intermediary_tree = get_tree(self.new_intermediary_code, gen_name=f'boba_{self.boba_parser.lang.lang[0]}')
        
        # generate new boba spec (need diff)
        self.template_config_tree = get_tree(self.boba_parser.code_parser.raw_spec)
        self.boba_var_to_tree_options = parse_boba_var_config_ast(self.template_config_tree)
        self.var_tree_mappings, self.template_spec_tree_to_boba_choice_var = self.handle_boba_vars()
        self.new_raw_spec = chunk_code(self.boba_parser.code_parser.raw_spec, self.var_tree_mappings)
        
        self.configure({"matcher": "classic",
                        "generator": "python",
                        "priority_queue": "python"})
        
        self.spec_diff = self.get_spec_diff()
        self.spec_classifier = self.spec_diff.createRootNodesClassifier()
        self.template_builder = NewTemplateBuilder(self.template_code_pos,
                                                   self.new_intermediary_code,
                                                   self.new_raw_spec)
    def get_spec_diff(self):
        src = TreeContext()
        src.root = self.template_config_tree
        src.root.parent = None
        dst = PythonTreeGenerator().generate_tree(self.new_raw_spec)
        matcher = MatcherFactory("classic").get_matcher()
        matcher.configure({"priority_queue": "python"})

        mappings = matcher.match(src.root, dst.root,  MappingStore(src.root, dst.root))
        edit_script = ChawatheScriptGenerator.compute_actions(mappings)
        return Diff(src, dst, mappings, edit_script)
    

    def handle_boba_vars(self) -> List[Tuple[str, Tree]]:
        boba_var_to_mapped_tree: Dict[str] = defaultdict(set)
        for boba_var, mapped in self.diff.mappings.src_to_dst_boba_map.items():
            mapped_tree = mapped
            if mapped_tree.node_type == 'string':
                boba_var_to_mapped_tree[boba_var.label].add(mapped_tree.label)
            else:
                boba_var_to_mapped_tree[boba_var.label].add(mapped_tree.ast_code)
        
        mappings: List[Tuple[str, Tree]] = [] 
        tree_to_boba_choice_var = {}
        for k, v in boba_var_to_mapped_tree.items():
            if len(v) > 1:
                print(f'Multiple values for same boba var: {k}\n{v}')
            choice_idx = self.history.decision_dict[k][1]
            v_tree = self.boba_var_to_tree_options[k][choice_idx]
            replace_v = v.pop()
            if self.boba_parser.lang.lang[0] == "python":
                var_unchanged = eval(str(json.loads(v_tree.ast_code))) == eval(replace_v)
            else:
                var_unchanged = str(json.loads(v_tree.ast_code)) == replace_v
            if var_unchanged:
                continue
            mappings.append((json.dumps(replace_v),  v_tree))
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
        

    def get_line_marks(self, 
                       src_code_lines: List[str],
                       dst_code_lines: List[str]) -> Tuple[Dict[int, List[LinePosMark]],
                                                           Dict[int, List[LinePosMark]]]:
        src_line_to_mark: Dict[int, List[LinePosMark]] = defaultdict(list)
        dst_line_to_mark: Dict[int, List[LinePosMark]] = defaultdict(list)
        
        self._get_line_marks_helper(src_code_lines,
                                   dst_code_lines,
                                   self.spec_diff,
                                   self.spec_classifier,
                                   get_pos_src=self.template_code_pos.get_template_boba_conf_pos_from_u,
                                   get_pos_dst=self.template_builder.new_template_code_pos.get_template_boba_conf_pos_from_u,
                                   src_line_to_mark=src_line_to_mark,
                                   dst_line_to_mark=dst_line_to_mark
                                   ) 
        
        for t in self.diff.src.root.pre_order():
            pos = self.template_code_pos.get_template_pos_from_u(t)
            if t in self.classifier.get_updated_srcs():
                self.add_line_mark(pos, src_code_lines, src_line_to_mark, self.UPDATE_TAG)
            if t in self.classifier.get_deleted_srcs():
                self.add_line_mark(pos, src_code_lines, src_line_to_mark, self.DEL_TAG)

        i_prime_preorder = self.new_intermediary_tree.pre_order()
        for t in self.diff.dst.root.pre_order():
            i_t = next(i_prime_preorder)
            pos = self.template_builder.new_template_code_pos.get_template_pos_from_u(i_t)
            if t in self.classifier.get_updated_dsts():
                self.add_line_mark(pos, dst_code_lines, dst_line_to_mark, self.UPDATE_TAG)
            if t in self.classifier.get_inserted_dsts():
                self.add_line_mark(pos, dst_code_lines, dst_line_to_mark, self.INSERT_TAG)
        # go through positions in changed dicionary  
        return src_line_to_mark, dst_line_to_mark
    
    def write_to_file(self, f1, f2, t, t_prime):
        with open(f1, 'w') as f:
            f.write(t)
        with open(f2, 'w') as f:
            f.write(t_prime)
        print(f'saved to {f1}')
        print(f'saved to {f2}')
        
        
        
if __name__ == "__main__":
    from src.utils import load_parser_example
    
    from src.utils import load_parser_example, read_universe_file, DATA_DIR
    import os.path as osp

    dataset, ext = 'hurricane', 'R'
    save_file = osp.join(DATA_DIR, f'{dataset}_template_parser_obj_0804.pickle')
    ps = load_parser_example(dataset, ext, None, run_parser_main=True)
    # ps._parse_blocks()
    universe_num = 3
    universe_code = read_universe_file(universe_num, dataset, ext)
    line_diff = TemplateDiff(ps, universe_code, universe_num)
    res = line_diff.run()