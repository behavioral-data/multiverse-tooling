from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
import difflib
from typing import Dict, List, Tuple
from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.diff.actions.tree_classifier import TreeClassifier
from src.gumtree.main.matchers.mapping_store import MappingStore

from src.gumtree.main.trees.tree_utils import PreOrderIterator, preorder

from src.boba.codeparser import BlockCode

def cumsum(code_blocks: List[BlockCode]):
    r, s = [], 0
    for code_block in code_blocks:
        l = code_block.code_num_lines
        r.append(l + s)
        s += l
    return r

class BlockInfo:
    def __init__(self, blocks: List[BlockCode]):
        self.blocks = blocks
        self.block_to_ind: Dict[str, int] = {str(blk): i for i, blk in enumerate(blocks)}
        self.block_boundaries: List[int] = cumsum(self.blocks)        
            
        
class GenerateTemplate:
    def __init__(self,
                 intermediary_blocks: BlockInfo,
                 template_blocks: BlockInfo,
                 intermediary_code_lines: List[str],
                 uprime_code_lines: List[str]
                 ):
        self.intermediary_blocks = intermediary_blocks
        self.template_blocks = template_blocks
        self.intermediary_code_lines = intermediary_code_lines
        self.uprime_code_lines = uprime_code_lines
        
        
    def get_boundaries(self):
        boundaries = self.intermediary_blocks.block_boundaries[:-1]
        """
        case1: matched at first line
        case2: inserted at boundary
            look for closest one th
        case3: deleted at boundary
        """
        new_boundaries = []
        diffs = list(difflib._mdiff(self.intermediary_code_lines, 
                                    self.uprime_code_lines))
        add_next = False
        insert_start = None
        for i, (old, new, changed) in enumerate(diffs):
            # case 3
            if add_next and new[0]:
                new_boundaries.append(new[0])
            # case 1
            elif old[0] and new[0]:
                if old[0] - 1 == 0 or old[0] - 1 in boundaries:
                    if insert_start is None:
                        new_boundaries.append(new[0] - 1)
                    else:
                        new_boundaries.append(insert_start)
                insert_start = None
            # case 3
            elif old[0] and not new[0]:
                if old[0]-1 == 0 or old[0]-1 in boundaries:
                    add_next = True
            elif new[0] and not old[0]:
                if insert_start is None:
                    insert_start = new[0] - 1
        return new_boundaries + [len(self.uprime_code_lines)]
    
    def generate_template_code(self):
        strs = []
        uprime_boundaries = self.get_boundaries()
        cur_template_len = 0
        block_offsets = []
        for code_block in self.template_blocks.blocks:
            if str(code_block) not in self.intermediary_blocks.block_to_ind:
                s = code_block.block_prefix + code_block.code_str
                strs.append(s)
                cur_template_len += s.count('\n')
            else:
                ind = self.intermediary_blocks.block_to_ind[str(code_block)]
                start, end = uprime_boundaries[ind], uprime_boundaries[ind+1]
                offset = cur_template_len + code_block.block_prefix.count('\n') - start
                block_offsets.append((str(code_block), offset))
                s = code_block.block_prefix + '\n'.join(self.uprime_code_lines[start: end]) + '\n'
                strs.append(s)
                cur_template_len += s.count('\n')
        return ''.join(strs)[:-1], block_offsets, uprime_boundaries[1:]

    