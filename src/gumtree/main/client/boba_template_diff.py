import bisect
from collections import defaultdict
from functools import partial
from typing import List

from src.boba.parser import History, Parser
from src.boba.codeparser import BlockCode
from src.gumtree.main.diff.diff import Diff
from src.gumtree.main.client.line_diff import LineDiff, Pos

from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.client.template_builder import BlockInfo, GenerateTemplate


# TODO 07/29/2022 parse the template file into AST, then make changes to the corresponding nodes ...
# * we can just parse the boba spec into ast so that we know where to make the corresponding changes
# * updates in universe need to be propagated back to the template file


def clean_code_blocks(code_blocks: List[BlockCode]):
    count_block = defaultdict(int)
    ret = []
    for blk in code_blocks:
        if str(blk) in count_block:
            new_name = blk.dec_name + f'_{count_block[str(blk)]}'
            if blk.dec_name == blk.opt_name:
                blk.opt_name = new_name
            blk.dec_name = new_name

        else:
            count_block[str(blk)] += 1
        ret.append(blk)
    return ret

    
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
        i_code_blocks: List[BlockCode] = clean_code_blocks(self.boba_parser.blocks_code[self.universe_num - 1])
        template_code_blocks: List[BlockCode] = clean_code_blocks(self.boba_parser.code_parser.all_blocks)
        with open(self.boba_parser.fn_script, 'r') as f:
            self.template_code = f.read()
        self.template_code_lines = self.template_code.split('\n')
        self.src_code_lines = self.src_code.split('\n')
        self.dst_code_lines = self.dst_code.split('\n')
        self.i_blocks = BlockInfo(i_code_blocks)
        self.template_blocks = BlockInfo(template_code_blocks)
        self.diff: Diff = self.get_diff()
        self.classifier = self.diff.createRootNodesClassifier()
    
    def get_i_t_block_offset(self):
        offsets = []
        i_boundaries = [0] + self.i_blocks.block_boundaries
        t_boundaries = [0] + self.template_blocks.block_boundaries
        for ind_i, blk in enumerate(self.i_blocks.blocks):
            start_line = i_boundaries[ind_i]
            ind_t = self.template_blocks.block_to_ind[str(blk)]
            blk_t = self.template_blocks.blocks[ind_t]
            template_start_line = t_boundaries[ind_t]
            extra = blk_t.block_prefix.count('\n')
            offsets.append((str(blk), template_start_line + extra - start_line))
        return offsets
    
    def run(self):        
        gb = GenerateTemplate(self.i_blocks,
                              self.template_blocks,
                              self.src_code_lines,
                              self.dst_code_lines)
        
        self.new_code, self.uprime_tprime_block_offsets, self.uprime_boundaries = gb.generate_template_code()
        self.i_t_block_offsets = self.get_i_t_block_offset()
        self.new_code_lines = self.new_code.split('\n')
        

        get_pos_src = partial(self.get_pos, bounds=self.i_blocks.block_boundaries,
                              offsets=self.i_t_block_offsets)
        get_pos_dst = partial(self.get_pos, bounds=self.uprime_boundaries,
                              offsets=self.uprime_tprime_block_offsets)
        src_str_lines, dst_str_lines = self.produce(self.template_code_lines, self.new_code_lines, get_pos_src, get_pos_dst)
        self.write_code(src_str_lines, dst_str_lines, self.template_code, self.new_code)

        
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
    
        
if __name__ == "__main__":
    from src.utils import load_parser_example
    
    from src.utils import load_parser_example, read_universe_file, DATA_DIR
    import os.path as osp

    dataset, ext = 'fertility2', 'py'
    save_file = osp.join(DATA_DIR, f'{dataset}_template_parser_obj_0802.pickle')
    ps = load_parser_example(dataset, ext, save_file, run_parser_main=True)
    # ps._parse_blocks()
    universe_num = 3
    universe_code = read_universe_file(universe_num, dataset, ext)
    line_diff = TemplateDiff(ps, universe_code, universe_num)
    res = line_diff.run()