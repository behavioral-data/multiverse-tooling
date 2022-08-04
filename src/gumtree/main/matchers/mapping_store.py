from __future__ import annotations
from collections.abc import Set
from typing import (
    Collection,
    Dict,
    List,
    Iterable,
    Tuple,
    TYPE_CHECKING
)
from src.gumtree.main.trees.tree_utils import HNIterator 

if TYPE_CHECKING:
    from src.gumtree.main.trees.tree import Tree


class MappingSet(Set):
        def __init__(self, values: Collection[Tree], ms: MappingStore) -> None:
            self.it = HNIterator(values)
            self.ms = ms
            self.values = values
        
        def has_next(self):
            return self.it.has_next()
        
        def __next__(self) -> Tuple[Tree, Tree]:
            src = next(self.it)
            if src is None: return None
            return (src, self.ms.src_to_dst.get(src))
        
        def __len__(self):
            return len(self.ms.src_to_dst.keys())
    
        def __iter__(self) -> Iterable[Tree, Tree]: 
            return self
        
        def __contains__(self, value: Tree):
            return value in self.values
        
# * 07/27 potentially need to add boba mapping store class to map one node to multiple other nodes as candidates (only for boba variables though)
class MappingStore:
    def __init__(self, src: Tree, dst: Tree):
        self.src = src
        self.dst = dst
        self.src_to_dst: Dict[Tree, Tree] = {}
        self.dst_to_src: Dict[Tree, Tree] = {}
        self.src_to_dst_boba_map: Dict[Tree, Tree] = {}
        self.dst_to_src_boba_map: Dict[Tree, Tree] = {}
        
    @classmethod
    def init_from_mapping_store(cls, ms: MappingStore):
        new_ms = cls(ms.src, ms.dst)
        for m in ms:
            new_ms.add_mapping(m[0], m[1])
        return new_ms
        
    def size(self):
        return len(self.src_to_dst)
    
    def add_boba_mapping(self, src: Tree, dst: Tree):
        self.src_to_dst_boba_map[src] = dst
        self.dst_to_src_boba_map[dst] = src
        
    def add_mapping(self, src: Tree, dst: Tree):
        self.src_to_dst[src] = dst
        self.dst_to_src[dst] = src
        
    def add_mapping_recursively(self, src: Tree, dst: Tree):
        self.add_mapping(src, dst)
        for i in range(len(src.children)):
            self.add_mapping_recursively(src.children[i], dst.children[i])
        
    def remove_mapping(self, src: Tree, dst: Tree):
        self.src_to_dst.pop(src, None)
        self.dst_to_src.pop(dst, None)
        
    def get_dst_for_src(self, src: Tree) -> Tree:
        return self.src_to_dst.get(src, None)
    
    def get_src_for_dst(self, dst: Tree) -> Tree:
        return self.dst_to_src.get(dst, None)
    
    def is_src_mapped(self, src: Tree):
        return src in self.src_to_dst
    
    def is_dst_mapped(self, dst: Tree):
        return dst in self.dst_to_src
    
    def are_both_unmapped(self, src: Tree, dst: Tree):
        return not(self.is_src_mapped(src) or self.is_dst_mapped(dst))
    
    def are_srcs_unmapped(self, srcs: List[Tree]):
        for src in srcs:
            if self.is_src_mapped(src):
                return False
        return True
    
    def are_dsts_unmapped(self, dsts: List[Tree]):
        for dst in dsts:
            if self.is_dst_mapped(dst):
                return False
        return True
    
    def has_unmapped_src_chilren(self, t: Tree):
        for c in t.get_descendents():
            if not self.is_src_mapped(c):
                return True
        return False
    
    def has_unmapped_dst_chilren(self, t: Tree):
        for c in t.get_descendents():
            if not self.is_dst_mapped(c):
                return True
        return False
    
    def has(self, src: Tree, dst: Tree):
        return self.src_to_dst[src] == dst
    
    def is_mapping_allowed(self, src: Tree, dst: Tree):
        return src.has_same_type(dst) and self.are_both_unmapped(src, dst)
        
    def as_set(self) -> MappingSet:
        return MappingSet(self.src_to_dst.keys(), self)
    
    def __iter__(self) -> Iterable[Tuple[Tree, Tree]]:
        return iter(self.as_set())
        
    def __str__(self):
        ret = []
        for m in self:
            s = f"{str(m[0])} -> {str(m[1])}"
            ret.append(s)
        return "\n".join(ret)