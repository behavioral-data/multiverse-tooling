from __future__ import annotations
from abc import ABC
import bisect
import chunk
from dataclasses import dataclass
from typing import Dict, List, Tuple
from src.gumtree.main.trees.tree import Tree
from src.boba.codeparser import Block, Chunk
from src.gumtree.main.matchers.mapping_store import MappingStore

from src.gumtree.main.trees.tree_utils import IteratorHandler


@dataclass
class OffsetsFromBobaVar:
    chunk_pos: List[int]
    offsets: List[int]  #offset is u to template difference
    boba_vars: List[str]
    boba_var_code_strs: List[str]
    
    def get_offset(self, pos: int):
        bs_left = self.offsets[bisect.bisect_left(self.chunk_pos, pos)]
        return bs_left
    
    @classmethod
    def init_from_tree_chunks(cls, tchunks: List[TreeChunk]):
        cur_pos = 0
        cur_offset = 0
        chunk_pos = []
        offsets = []
        boba_vars = []
        boba_var_code_strs = []
        for tc in tchunks:
            cur_pos += tc.code_len
            if tc.boba_var != '':
                chunk_pos.append(cur_pos)
                offsets.append(cur_offset)
                
                cur_pos += len(tc.boba_var_code_str)
                chunk_pos.append(cur_pos)
                offsets.append(None) #should not have an offset when it is a boba variable
                cur_offset += len(tc.boba_var_code_str) - len('{{' + tc.boba_var + '}}') 
                boba_vars.append(tc.boba_var)
                boba_var_code_strs.append(tc.boba_var_code_str)
        if cur_pos != chunk_pos[-1]:
            chunk_pos.append(cur_pos)
            offsets.append(cur_offset)
        return cls(chunk_pos, offsets, boba_vars, boba_var_code_strs)
    
    @classmethod
    def init_from_mapped_vars(cls, code_str, mapped_vars: List[MappedBobaVar]):
        cur_offset = 0
        chunk_pos = []
        offsets = []
        boba_vars = []
        boba_var_code_strs = []
        mapped_vars.sort(key=lambda x: x.pos)
        for mbv in mapped_vars:
            chunk_pos.append(mbv.pos)
            chunk_pos.append(mbv.end_pos)
            offsets.append(cur_offset)
            offsets.append(None)            
            cur_offset +=  mbv.length -  len('{{' + mbv.boba_var + '}}')
            boba_vars.append(mbv.boba_var)
            boba_var_code_strs.append(mbv.get_str(code_str))
        if len(code_str) != chunk_pos[-1]:
            chunk_pos.append(len(code_str))
            offsets.append(cur_offset)
        return cls(chunk_pos, offsets, boba_vars, boba_var_code_strs)


@dataclass            
class MappedBobaVar:
    boba_var: str
    boba_opt_str: str
    start_tree: Tree = None
    end_tree: Tree = None
    code_start_pos: int = None
    code_end_pos: int = None  
    
    @property
    def metadata(self) -> Dict:
        data = {}
        if self.start_tree is not None and self.end_tree is not None:
            data = {
                "lineno": self.start_tree.metadata.get("lineno"),
                "col_offset": self.start_tree.metadata.get("col_offset"),
                "end_lineno": self.end_tree.metadata.get("end_lineno"),
                "end_col_offset": self.end_tree.metadata.get("end_col_offset"),
            }
        return data
    
    def get_str(self, code_str: str):
        return code_str[self.pos: self.end_pos]
    
    @property
    def length(self):
        return self.end_pos - self.pos
    
    @property
    def pos(self):
        return self.start_tree.pos if self.start_tree is not None else self.code_start_pos
    
    @property
    def end_pos(self):
        return self.end_tree.end_pos if self.end_tree is not None else self.code_end_pos
    
    
def get_tree_chunks_from_mapping(ms: MappingStore, tchunks: List[TreeChunk]):
    """
    We want to loop preorder and match boba var.
    If the node is part of a boba var and it is mapped include it
    """
    boba_vars: List[MappedBobaVar] = []
    unmapped: List[TreeChunk] = []
    preorder_iter = IteratorHandler(ms.src.pre_order())
    cur_ind = 0
    for tc_ind, tc in enumerate(tchunks):
        if tc.boba_var != '' and tc.boba_var != '_n':
            if len(tc.boba_var_trees) > 0: # has non empty boba var option
                src_boba_var_trees = tc.boba_var_trees
                i = 0
                dst = None
                while i < len(src_boba_var_trees):
                    t = src_boba_var_trees[i]
                    dst = ms.get_dst_for_src(t)
                    if dst:
                        break
                    i += 1
                start_tree = dst
                j = len(src_boba_var_trees) - 1
                while j >= 0:
                    t = src_boba_var_trees[j]
                    dst = ms.get_dst_for_src(t)
                    if dst:
                        break
                    j -= 1
                end_tree = dst
                if start_tree is not None and end_tree is not None and j >= i:
                    boba_vars.append(MappedBobaVar(tc.boba_var, 
                                                   tc.boba_var_code_str, 
                                                   start_tree, 
                                                   end_tree))
                else:
                    unmapped.append(tc)
            else: # empty string
                has_tree_ind = tc_ind
                while has_tree_ind >= 0:
                    if len(tchunks[has_tree_ind].all_trees) == 0:
                        has_tree_ind -= 1
                    else:
                        break
                prev_tree = tchunks[has_tree_ind].all_trees[-1]
                prev_tree_save = prev_tree
                while prev_tree and (not prev_tree.is_leaf() or not ms.is_src_mapped(prev_tree)):
                    prev_tree = preorder_iter.get_prev(prev_tree)
                dst_tree = ms.get_dst_for_src(prev_tree)
                src_var_pos = cur_ind + tc.code_len
                dst_var_pos = dst_tree.end_pos + (src_var_pos - prev_tree_save.end_pos)
                boba_vars.append(MappedBobaVar(tc.boba_var, tc.boba_var_code_str,
                                               code_start_pos=dst_var_pos,
                                               code_end_pos=dst_var_pos))
                
        cur_ind += tc.all_code_len
    return boba_vars, unmapped
                      

def get_tree_chunks_from_blocks(src: Tree, blocks: List[Block], decision_dict):
    chunks = []  
    for blk in blocks:
        chunks.extend(blk.chunks)
    return get_tree_chunks(src, chunks, decision_dict)
    
def get_tree_chunks(src: Tree, 
                    chunks: List[Chunk], 
                    decision_dict: Dict[str, Tuple[str, int]]) -> List[TreeChunk]:
    chunks_ind = 0
    cur_tree_pos = 0
    cur_trees = []
    tree_chunks: List[TreeChunk] = []
    pre_order_iter = list(src.pre_order())
    cur_iter_ind = 0
    last_boba_t = None
    while cur_iter_ind < len(pre_order_iter):
        t = pre_order_iter[cur_iter_ind]
        if t != last_boba_t:
            cur_trees.append(t)
        if t.is_leaf():
            cur_chunk = chunks[chunks_ind]
            end_pos = len(cur_chunk.code) + cur_tree_pos
            if (cur_iter_ind + 1 < len(pre_order_iter) and pre_order_iter[cur_iter_ind + 1].pos >= end_pos):
                if cur_chunk.variable == '':
                    tree_chunks.append(TreeChunk(cur_chunk.code, cur_trees))
                    cur_tree_pos += len(cur_chunk.code)
                    last_boba_t = cur_trees[-1] if cur_trees else last_boba_t
                else:
                    boba_var_code_str = decision_dict[cur_chunk.variable][0]
                    if boba_var_code_str == '':
                        tree_chunks.append(TreeChunk(cur_chunk.code, cur_trees, [], cur_chunk.variable, ''))
                        cur_tree_pos += len(cur_chunk.code)
                        cur_iter_ind -= 1
                        last_boba_t = cur_trees[-1] if cur_trees else last_boba_t
                    else:
                        boba_var_start_pos = len(cur_chunk.code) + cur_tree_pos
                        cur_tree_pos = len(cur_chunk.code) + cur_tree_pos + len(boba_var_code_str)
                        boba_trees = []
                        while (cur_iter_ind + 1 < len(pre_order_iter)) and not(t.is_leaf() and pre_order_iter[cur_iter_ind + 1].pos >= cur_tree_pos):
                            cur_iter_ind += 1
                            t =  pre_order_iter[cur_iter_ind]
                            boba_trees.append(t)
                        last_boba_t = t
                        cur_iter_ind -= 1
                        tree_chunks.append(TreeChunk(cur_chunk.code,
                                                     cur_trees, 
                                                     boba_trees,
                                                     cur_chunk.variable,
                                                     boba_var_code_str,
                                                     boba_var_start_pos=boba_var_start_pos,
                                                     boba_var_end_pos=boba_var_start_pos + len(boba_var_code_str)
                                                    ))
                cur_trees = []
                chunks_ind += 1
        cur_iter_ind +=1
        
    tree_chunks.append(TreeChunk(cur_chunk.code, cur_trees))
    return tree_chunks


class TreeChunk:
    def __init__(self, 
                 code_str: str,
                 trees: List[Tree], 
                 boba_var_trees: List[Tree]=None,
                 boba_var: str=None,
                 boba_var_code_str: str=None,
                 boba_var_start_pos: int=None,
                 boba_var_end_pos: int=None):
        self._trees = []
        self._boba_var_trees = []
        self.code_str = code_str
        self.boba_var = boba_var if boba_var is not None else ''
        self.boba_var_code_str = boba_var_code_str if boba_var_code_str is not None else ''
        self.trees: List[Tree] = trees
        self.boba_var_trees: List[Tree] = boba_var_trees if boba_var_trees is not None else []
        self.all_trees = self.trees + self.boba_var_trees
        self.all_code_str = self.code_str + self.boba_var_code_str
        self.boba_var_start_pos = boba_var_start_pos
        self.boba_var_end_pos = boba_var_end_pos
       
    def __repr__(self):
        return f'TreeChunk(boba_var={self.boba_var}, option={self.boba_var_code_str}, trees={self.trees}, boba_var_trees={self.boba_var_trees})'
    
    @property
    def trees(self):
        return self._trees
    
    @trees.setter
    def trees(self, ts: List[Tree]):
        self._trees = ts
        for t in ts:
            t.metadata['chunk'] = self
    
    @property
    def boba_var_trees(self):
        return self._boba_var_trees
    
    @boba_var_trees.setter
    def boba_var_trees(self, boba_ts: List[Tree]):
        self._boba_var_trees = boba_ts
        for t in boba_ts:
            t.metadata['boba_var'] = self.boba_var
    
    @property
    def code_len(self):
        return len(self.code_str)
    
    @property
    def all_code_len(self):
        return self.code_len + self.boba_var_len
    
    @property
    def boba_var_len(self):
        return len(self.boba_var_code_str)
         
    
    