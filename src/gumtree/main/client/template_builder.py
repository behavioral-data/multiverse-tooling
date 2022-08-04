from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
import difflib
from typing import Dict, List, Tuple
from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.diff.actions.tree_classifier import TreeClassifier
from src.gumtree.main.matchers.mapping_store import MappingStore

from src.gumtree.main.trees.tree_utils import PreOrderIterator, preorder

from src.boba.codeparser import Block, BlockCode

def cumsum(code_blocks: List[BlockCode]):
    r, s = [], 0
    for code_block in code_blocks:
        l = code_block.code_num_lines
        r.append(l + s)
        s += l
    return r

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
    
    
    def calculate_offset(self, other: BlockInfo):
        assert set(self.block_to_ind.keys()).issubset(other.block_to_ind.keys()), "need to be subset of other block info"
        offsets = []
        for i, blk in enumerate(self.blocks):
            start_line = self.block_start_boundaries[i]
            j = other.block_to_ind[str(blk)]
            other_blk = other.blocks[j]
            other_start_line = other.block_start_boundaries[j]
            other_prefix_cnt = other_blk.block_prefix.count('\n')
            offsets.append((str(blk), other_start_line + other_prefix_cnt - start_line))
        return offsets
    
    
class NewTemplateBuilder:
    def __init__(self,
                 intermediary_blocks: BlockInfo,
                 template_blocks: BlockInfo,
                 intermediary_code_lines: List[str],
                 new_intermediary_code_lines: List[str],
                 new_boba_config_str: str
                 ):
        self.intermediary_blocks = intermediary_blocks
        self.template_blocks = template_blocks
        self.intermediary_code_lines = intermediary_code_lines
        self.new_intermediary_code_lines = new_intermediary_code_lines
        self.new_boba_config_str = new_boba_config_str
        
        self.new_template_code: str = None
        self.new_template_blocks: BlockInfo = None
        self.new_intermediary_blocks: BlockInfo = None
        self.generate()
        self.new_inter_new_template_offset = self.new_intermediary_blocks.calculate_offset(self.new_template_blocks)
        
    def get_updated_block_start_boundaries(self,
                                           src_code_lines: List[str],
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
                        
        self.new_template_code = ''.join(strs)[:-1]
        self.new_template_blocks = BlockInfo(new_template_code_blocks)
        self.new_intermediary_blocks = BlockInfo(new_intermediary_code_blocks)

    