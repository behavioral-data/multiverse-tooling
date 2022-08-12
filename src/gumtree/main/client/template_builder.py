from __future__ import annotations
import bisect
from copy import deepcopy
from dataclasses import dataclass
import difflib
from typing import Dict, List, Tuple
from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.diff.actions.tree_classifier import TreeClassifier
from src.gumtree.main.matchers.mapping_store import MappingStore

from src.gumtree.main.trees.tree_utils import PreOrderIterator, preorder

from src.boba.codeparser import Block, BlockCode

from src.gumtree.main.gen.python_tree_generator import get_positions

def cumsum(code_blocks: List[BlockCode]):
    r, s = [], 0
    for code_block in code_blocks:
        l = code_block.code_num_lines
        r.append(l + s)
        s += l
    return r

@dataclass(frozen=True, eq=True)
class Pos:
    lineno: int = -1
    col_offset: int = -1
    end_lineno: int = -1
    end_col_offset: int = -1
    
        
    def get_code(self, code: str):
        if self.lineno == -1:
            return ""
        code_lines = code.encode(encoding = 'UTF-8', errors = 'strict')
        code_lines = code.split('\n')
        code_lines = code_lines[self.lineno - 1 : self.end_lineno]
        if len(code_lines) == 1:
            return code_lines[0][self.col_offset: self.end_col_offset]
        else:
            code_lines[0] = code_lines[0][self.col_offset:]
            code_lines[-1] = code_lines[-1][:self.end_col_offset]
            return "\n".join(code_lines)
        
        
class BlockInfo:
    """
    The boundaries of blocks correspond to inds and not line numbers: Inds start at 0. 
    Line nums start at 1
    """
    def __init__(self, blocks: List[BlockCode]):
        self.blocks = blocks
        self.block_to_ind: Dict[str, int] = {str(blk): i for i, blk in enumerate(blocks)}
        self.block_boundaries: List[int] = cumsum(self.blocks)        
        self.block_start_boundaries = [0] + self.block_boundaries[:-1]
    
    def get_block_start(self, blk_name: str):
        ind = self.block_to_ind[blk_name]
        return self.block_start_boundaries[ind] + self.blocks[ind].block_prefix.count('\n')
    
    
    def calculate_offset(self, other: BlockInfo) -> List[Tuple[str, int]]:
        assert set(self.block_to_ind.keys()).issubset(other.block_to_ind.keys()), "need to be subset of other block info"
        offsets = []
        for i, blk in enumerate(self.blocks):
            start_line = self.block_start_boundaries[i]
            j = other.block_to_ind[str(blk)]
            other_blk = other.blocks[j]
            other_start_line = other.block_start_boundaries[j]
            other_prefix_cnt = other_blk.block_prefix.count('\n')
            other_start_line += other_prefix_cnt
            offsets.append((str(blk), other_start_line, start_line))
        return offsets



class CodePos:    
    def __init__(self, 
                 u_code_str: str,
                 template_code_str: str,
                 u_block_info: BlockInfo,
                 template_block_info: BlockInfo):
        self.u_code_str = u_code_str
        self.template_code_str = template_code_str
        self.u_block_info = u_block_info
        self.template_block_info = template_block_info
        self.template_line_positions = get_positions(self.template_code_str)
        self.u_line_positions = get_positions(self.u_code_str)
        self.bounds = self.u_block_info.block_boundaries
        self.block_line_offsets = self.u_block_info.calculate_offset(self.template_block_info)
        self.block_pos_offsets = self.get_block_pos_offsets(self.block_line_offsets)
    
    def get_block_pos_offsets(self, block_offsets):
        ret = []
        for block_name, template_ind, u_ind in block_offsets:
            pos_offset = self.template_line_positions[template_ind] - self.u_line_positions[u_ind]
            ret.append((block_name, pos_offset))
        return ret
    
    def get_pos_offset_from_pos(self, pos):
        line = bisect.bisect_right(self.u_line_positions, pos) + 1
        return self.get_pos_offset_from_line(line)
    
    def get_pos_offset_from_line(self, lineno):
        ind = bisect.bisect_left(self.bounds, lineno-1)
        return self.block_pos_offsets[ind][1]
    
    def get_pos_offset(self, t: Tree) -> int:
        ind = self.get_block_ind(t)
        if ind == -1:
            return -1
        return self.block_pos_offsets[ind][1]
    
    def get_offset_from_line_offset(self, line_offset: int, 
                                    line_positions: List[int]) -> int:
        return line_positions[line_offset]
    
    def get_boba_config_pos_offset(self) -> int:
        line_offset = self.template_block_info.get_block_start('BOBA_CONFIG')
        return self.get_offset_from_line_offset(line_offset, self.template_line_positions)
    
    def get_block_ind(self, t: Tree):
        lineno = t.metadata.get("lineno")
        if lineno is None:
            return -1
        ind = bisect.bisect_left(self.bounds, lineno-1)
        return ind
    
    def get_u_block_starting_line(self, t: Tree):
        ind = self.get_block_ind(t)
        if ind == -1:
            return ind
        return self.block_line_offsets[ind][2] # starting line of u
    
    def get_u_block_starting_line_pos(self, t: Tree):
        starting_line = self.get_u_block_starting_line(t)
        return self.get_offset_from_line_offset(starting_line, self.u_line_positions)
    
    def get_line_offset(self, t: Tree) -> int:
        ind = self.get_block_ind(t)
        if ind == -1:
            return -1
        line_offset = self.block_line_offsets[ind][1] - self.block_line_offsets[ind][2]
        return line_offset
    
    def get_template_pos_from_u(self, t: Tree) ->  Pos:
        line_offset = self.get_line_offset(t)
        if line_offset == -1:
            return Pos()
        else:
            return Pos(t.metadata.get("lineno", -1) + line_offset,
                       t.metadata.get("col_offset", -1),
                       t.metadata.get("end_lineno", -1) + line_offset,
                       t.metadata.get("end_col_offset", -1))
            
    def get_template_boba_conf_pos_from_u(self, t: Tree) -> Pos:
        if t.metadata.get("lineno") is None:
            return -1
        else:
            offset = self.template_block_info.get_block_start('BOBA_CONFIG')
            return Pos(t.metadata.get("lineno", -1) + offset,
                   t.metadata.get("col_offset", -1),
                   t.metadata.get("end_lineno", -1) + offset,
                   t.metadata.get("end_col_offset", -1))
    
class NewTemplateBuilder:
    def __init__(self,
                 template_code_pos: CodePos,
                 new_intermediary_code: List[str],
                 new_boba_config_str: str
                 ):
        self.intermediary_blocks: BlockInfo = template_code_pos.u_block_info
        self.template_blocks: BlockInfo = template_code_pos.template_block_info
        self.intermediary_code_lines = template_code_pos.u_code_str.split('\n')
        self.new_intermediary_code = new_intermediary_code
        self.new_intermediary_code_lines = new_intermediary_code.split('\n')
        self.new_boba_config_str = new_boba_config_str
        
        self.new_template_code_pos: CodePos = self.generate()
        
    @staticmethod
    def get_updated_block_start_boundaries(src_code_lines: List[str],
                                           dst_code_lines: List[str],
                                           src_block_starts: List[int]
                                           ):
        """
        We leverage difflib mdiff.
        case1: matched at first line
        case2: deleted line
            a. We need to check if it is deleted within a block or 
            b. At the boundary of new block.
        case 3: inserted
            a. We need to check if it is inserted within a block (insert_start: None)
            b. At the start of a new block (we default to always including it as the start of a new block)
                insert_start: line_num
        """
        dst_block_starts = []
        add_next = False
        insert_start = None
        for old, new, _ in difflib._mdiff(src_code_lines,
                                          dst_code_lines):
            # case 2 (b)
            if add_next and new[0]:
                dst_block_starts.append(new[0])
            # case 1
            elif old[0] and new[0]:
                if old[0] - 1 in src_block_starts:
                    if insert_start is None:
                        dst_block_starts.append(new[0] - 1)
                    else: # case 3 (b)
                        dst_block_starts.append(insert_start)
                insert_start = None
            # case 2
            elif old[0] and not new[0]:
                if old[0] - 1 in src_block_starts:
                    add_next = True
            # case 3
            elif new[0] and not old[0]:
                if insert_start is None: 
                    insert_start = new[0] - 1
        return dst_block_starts
    
    
    def generate(self):
        new_intermediary_block_starts = self.get_updated_block_start_boundaries(
            src_code_lines=self.intermediary_code_lines,
            dst_code_lines=self.new_intermediary_code_lines,
            src_block_starts=self.intermediary_blocks.block_start_boundaries)
        new_intermediary_block_starts = new_intermediary_block_starts + [len(self.new_intermediary_code_lines)]
        
        strs = []
        cur_template_len = 0
        block_offsets: List[Tuple[str, int]] = []
        new_template_code_blocks: List[BlockCode] = []
        new_intermediary_code_blocks: List[BlockCode] = []
        
        for code_block in self.template_blocks.blocks:
            if str(code_block) not in self.intermediary_blocks.block_to_ind:
                if str(code_block) == 'BOBA_CONFIG':
                    s = code_block.block_prefix + self.new_boba_config_str
                else:
                    s = code_block.block_prefix + code_block.code_str
                new_template_code_blocks.append(code_block)
                strs.append(s)
                cur_template_len += s.count('\n')
            else:
                ind = self.intermediary_blocks.block_to_ind[str(code_block)]
                start, end = new_intermediary_block_starts[ind], new_intermediary_block_starts[ind+1]
                offset = cur_template_len + code_block.block_prefix.count('\n') - start
                block_offsets.append((str(code_block), offset))
                code_str = '\n'.join(self.new_intermediary_code_lines[start: end]) + '\n'
                s = code_block.block_prefix + code_str
                new_block_temp = BlockCode(code_block.dec_name, 
                                      code_block.opt_name,
                                      code_str,
                                      block_prefix=code_block.block_prefix)
                new_block_inter = BlockCode(code_block.dec_name, 
                                      code_block.opt_name,
                                      code_str
                                      )
                new_template_code_blocks.append(new_block_temp)
                new_intermediary_code_blocks.append(new_block_inter)
                strs.append(s)
                cur_template_len += s.count('\n')
                        
        new_template_code = ''.join(strs)[:-1]
        new_intermediary_blocks = BlockInfo(new_intermediary_code_blocks)
        new_template_blocks = BlockInfo(new_template_code_blocks)

        new_template_code_pos = CodePos(self.new_intermediary_code,
                                        new_template_code,
                                        new_intermediary_blocks,
                                        new_template_blocks)
        return new_template_code_pos
    