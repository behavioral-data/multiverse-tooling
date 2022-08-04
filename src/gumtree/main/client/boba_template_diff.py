import bisect
from collections import defaultdict
from functools import partial
import json
from typing import Dict, List, Tuple

from src.boba.parser import History, Parser
from src.boba.codeparser import BlockCode
from src.gumtree.main.diff.diff import Diff
from src.gumtree.main.client.line_diff import LineDiff, LinePosMark, Pos

from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.client.template_builder import BlockInfo, NewTemplateBuilder

from src.utils import OUTPUT_DIR
from src.gumtree.main.client.boba_utils import chunk_code, clean_code_blocks, get_tree, parse_boba_var_config_ast




    
class TemplateDiff(LineDiff):
    DEFAULT_GENERATOR = ("boba_python_template", "python")
    MATCHER =  "boba"
    PRIOIRITY_QUEUE = "python"

    def __init__(self, ps: Parser, universe_code: str, universe_num: int):
        
        self.boba_parser = ps
        self.universe_num = universe_num
        self.history: History = ps.history[universe_num - 1]
        intermediary_code = self.boba_parser.paths_code[self.history.path]
        configurations = {
            "generator": self.DEFAULT_GENERATOR,
            "matcher": self.MATCHER,
            "parser_history": self.history,
            "priority_queue": self.PRIOIRITY_QUEUE
        }
        super().__init__(intermediary_code, universe_code, configurations)
        
        intermediary_code_blocks: List[BlockCode] = clean_code_blocks(self.boba_parser.blocks_code[self.universe_num - 1])
        template_code_blocks: List[BlockCode] = clean_code_blocks(self.boba_parser.code_parser.all_blocks)
        self.intermediary_blocks = BlockInfo(intermediary_code_blocks)
        self.template_blocks = BlockInfo(template_code_blocks)
        
        
        self.src_code_lines = self.src_code.split('\n')
        self.dst_code_lines = self.dst_code.split('\n')
        with open(self.boba_parser.fn_script, 'r') as f:
            self.template_code = f.read()
        self.template_code_lines = self.template_code.split('\n')

        self.diff: Diff = self.get_diff()
        self.classifier = self.diff.createRootNodesClassifier()
        
        # generate intermediary code (need diff)
        self.new_intermediary_code = chunk_code(self.dst_code, 
                                                [('{{' + t.label + '}}', v) 
                                                 for t, v in self.diff.mappings.src_to_dst_boba_map.items()])
        self.new_intermediary_tree = get_tree(self.new_intermediary_code, gen_name='boba')
        
        # generate new boba spec (need diff)
        boba_config_tree = get_tree(self.boba_parser.code_parser.raw_spec)
        self.boba_var_to_tree_options = parse_boba_var_config_ast(boba_config_tree)
        mappings = self.handle_boba_vars()
        self.new_raw_spec = chunk_code(self.boba_parser.code_parser.raw_spec, mappings)
        
        self.configure({"matcher": "classic",
                        "generator": "python",
                        "priority_queue": "default"})
        
        self.spec_diff = Diff.compute_from_strs(self.boba_parser.code_parser.raw_spec, 
                                                self.new_raw_spec, self.generator,
                                                self.matcher, self.configurations)
        self.spec_classifier = self.spec_diff.createRootNodesClassifier()
    
    
    def handle_boba_vars(self) -> List[Tuple[str, Tree]]:
        boba_var_to_mapped_tree: Dict[str] = defaultdict(set)
        for boba_var, mapped in self.diff.mappings.src_to_dst_boba_map.items():
            mapped_tree = mapped
            if mapped_tree.node_type == 'string':
                boba_var_to_mapped_tree[boba_var.label].add(mapped_tree.label)
            else:
                boba_var_to_mapped_tree[boba_var.label].add(mapped_tree.ast_code)
        
        mappings = [] 
        for k, v in boba_var_to_mapped_tree.items():
            if len(v) > 1:
                print(f'Multiple values for same boba var: {k}\n{v}')
            choice_idx = self.history.decision_dict[k][1]
            v_tree = self.boba_var_to_tree_options[k][choice_idx]
            replace_v = v.pop()
            if eval(str(json.loads(v_tree.ast_code))) == eval(replace_v):
                continue
            mappings.append((json.dumps(json.loads(replace_v)),  v_tree))
        return mappings

    
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
        self.template_builder = NewTemplateBuilder(self.intermediary_blocks,
                                                   self.template_blocks,
                                                   self.src_code_lines,
                                                   self.new_intermediary_code.split('\n'),
                                                   self.new_raw_spec)
                
        src_str_lines, dst_str_lines = self.produce(self.template_code_lines, 
                                                    self.template_builder.new_template_code.split('\n'), 
                                                    )
        
        self.write_code(src_str_lines, 
                        dst_str_lines, 
                        self.template_code, 
                        self.template_builder.new_template_code)
        
        self.write_to_file(osp.join(OUTPUT_DIR, 'template.py'), 
                           osp.join(OUTPUT_DIR, 'template_changed.py'),
                           self.template_code, self.template_builder.new_template_code) 
        

    def get_line_marks(self, 
                       src_code_lines: List[str],
                       dst_code_lines: List[str]) -> Tuple[Dict[int, List[LinePosMark]],
                                                           Dict[int, List[LinePosMark]]]:
        src_line_to_mark: Dict[int, List[LinePosMark]] = defaultdict(list)
        dst_line_to_mark: Dict[int, List[LinePosMark]] = defaultdict(list)
        
        intermediary_template_offset = self.intermediary_blocks.calculate_offset(self.template_blocks)
        get_pos_src = partial(self.get_pos, 
                              bounds=self.intermediary_blocks.block_boundaries,
                              offsets=intermediary_template_offset)
        get_pos_dst = partial(self.get_pos, 
                              bounds=self.template_builder.new_intermediary_blocks.block_boundaries,
                              offsets=self.template_builder.new_inter_new_template_offset)
        
        t_boba_conf_offset = self.template_blocks.get_block_start('BOBA_CONFIG')
        t_prime_boba_conf_offset = self.template_builder.new_template_blocks.get_block_start('BOBA_CONFIG')
        
        get_pos_src_json = partial(self.get_pos_offset, offset=t_boba_conf_offset)
        get_pos_dst_json = partial(self.get_pos_offset, offset=t_prime_boba_conf_offset)
        
        self._get_line_marks_helper(src_code_lines,
                                   dst_code_lines,
                                   self.spec_diff,
                                   self.spec_classifier,
                                   get_pos_src=get_pos_src_json,
                                   get_pos_dst=get_pos_dst_json,
                                   src_line_to_mark=src_line_to_mark,
                                   dst_line_to_mark=dst_line_to_mark
                                   ) 
        
        for t in self.diff.src.root.pre_order():
            pos = get_pos_src(t)
            if t in self.classifier.get_updated_srcs():
                self.add_line_mark(pos, src_code_lines, src_line_to_mark, self.UPDATE_TAG)
            if t in self.classifier.get_deleted_srcs():
                self.add_line_mark(pos, src_code_lines, src_line_to_mark, self.DEL_TAG)

        i_prime_preorder = self.new_intermediary_tree.pre_order()
        for t in self.diff.dst.root.pre_order():
            i_t = next(i_prime_preorder)
            pos = get_pos_dst(i_t)
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
        
        
    def get_pos(self, t: Tree, bounds=None, offsets=None) -> Pos:
        if bounds is None:
            return super().get_pos(t)
        lineno = t.metadata.get("lineno")
        if lineno is None:
            return super().get_pos(t)
        ind = bisect.bisect_left(bounds, lineno-1)
        offset = offsets[ind][1]
        
        return Pos(t.metadata.get("lineno", -1) + offset,
                   t.metadata.get("col_offset", -1),
                   t.metadata.get("end_lineno", -1) + offset,
                   t.metadata.get("end_col_offset", -1))
    
    def get_pos_offset(self, t: Tree, offset:int):
        return Pos(t.metadata.get("lineno", -1) + offset,
                   t.metadata.get("col_offset", -1),
                   t.metadata.get("end_lineno", -1) + offset,
                   t.metadata.get("end_col_offset", -1))
        
        
if __name__ == "__main__":
    from src.utils import load_parser_example
    
    from src.utils import load_parser_example, read_universe_file, DATA_DIR
    import os.path as osp

    dataset, ext = 'fertility2', 'py'
    save_file = osp.join(DATA_DIR, f'{dataset}_template_parser_obj_0804.pickle')
    ps = load_parser_example(dataset, ext, save_file, run_parser_main=True)
    # ps._parse_blocks()
    universe_num = 3
    universe_code = read_universe_file(universe_num, dataset, ext)
    line_diff = TemplateDiff(ps, universe_code, universe_num)
    res = line_diff.run()