from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Set, TYPE_CHECKING
if TYPE_CHECKING:
    from src.gumtree.main.diff.diff import Diff
from src.gumtree.main.trees.tree import Tree

from src.gumtree.main.diff.actions.delete import Delete
from src.gumtree.main.diff.actions.insert import Insert
from src.gumtree.main.diff.actions.move import Move
from src.gumtree.main.diff.actions.tree_addition import TreeInsert
from src.gumtree.main.diff.actions.tree_delete import TreeDelete
from src.gumtree.main.diff.actions.update import Update



class TreeClassifier(ABC):
    
    def __init__(self, diff: Diff):
        self.diff = diff
        self.src_upd_trees: Set[Tree] = set()
        self.dst_upd_trees: Set[Tree] = set()
        self.src_mv_trees: Set[Tree] = set()
        self.dst_mv_trees: Set[Tree] = set()
        self.src_del_trees: Set[Tree] = set()

        self.dst_add_trees: Set[Tree] = set()
        self.classify()
        
    @abstractmethod
    def classify(self):
        pass 
    
    def changed_src_tree(self, t: Tree):
        return t in self.get_moved_srcs() or t in self.get_updated_srcs() or t in self.get_deleted_srcs()
    
    def changed_dst_tree(self, t: Tree):
        return t in self.get_moved_dsts() or t in self.get_updated_dsts() or t in self.get_inserted_dsts()
    
    def get_updated_srcs(self) -> Set[Tree]:
        return self.src_upd_trees
    
    def get_deleted_srcs(self) -> Set[Tree]:
        return self.src_del_trees
    
    def get_moved_srcs(self) -> Set[Tree]:
        return self.src_mv_trees
    
    def get_updated_dsts(self) -> Set[Tree]:
        return self.dst_upd_trees
    
    def get_inserted_dsts(self) -> Set[Tree]:
        return self.dst_add_trees
    
    def get_moved_dsts(self) -> Set[Tree]:
        return self.dst_mv_trees
    
    
class AllNodesClassifier(TreeClassifier):
    def classify(self):
        for a in self.diff.edit_script:
            if isinstance(a, Delete):
                self.src_del_trees.add(a.node)
            elif isinstance(a, TreeDelete):
                self.src_del_trees.add(a.node)
                self.src_del_trees.update(set(a.node.get_descendents()))
            elif isinstance(a, Insert):
                self.dst_add_trees.add(a.node)
            elif isinstance(a, TreeInsert):
                self.dst_add_trees.add(a.node)
                self.dst_add_trees.update(set(a.node.get_descendents()))
            elif isinstance(a, Update):
                self.src_upd_trees.add(a.node)
                self.dst_upd_trees.add(self.diff.mappings.get_dst_for_src(a.node))
            elif isinstance(a, Move):
                self.src_mv_trees.add(a.node)
                self.src_mv_trees.update(set(a.node.get_descendents()))
                self.dst_mv_trees.add(self.diff.mappings.get_dst_for_src(a.node))
                self.dst_mv_trees.update(set(self.diff.mappings.get_dst_for_src(a.node).get_descendents()))

class OnlyRootsClassifier(TreeClassifier):
    """
    Partition only root (of a complete subtree) moved, inserted, 
    updated or deleted nodes.

    """
    def classify(self):
        inserted_dsts: Set[Tree] = set()
        
        for a in self.diff.edit_script:
            if isinstance(a, Insert):
                inserted_dsts.add(a.node)
        
        deleted_srcs: Set[Tree] = set()
        
        for a in self.diff.edit_script:
            if isinstance(a, Delete):
                deleted_srcs.add(a.node)
        
            
        for a in self.diff.edit_script:
            if isinstance(a, TreeDelete):
                self.src_del_trees.add(a.node)
            if isinstance(a, Delete):
                if not(set(a.node.get_descendents()).issubset(deleted_srcs) 
                       and a.node.parent in deleted_srcs):    
                    self.src_del_trees.add(a.node)
            elif isinstance(a, Insert):
                if not(set(a.node.get_descendents()).issubset(inserted_dsts) 
                       and a.node.parent in inserted_dsts):  
                    self.dst_add_trees.add(a.node)
            elif isinstance(a, TreeInsert):
                self.dst_add_trees.add(a.node)
            elif isinstance(a, Update):
                self.src_upd_trees.add(a.node)
                self.dst_upd_trees.add(self.diff.mappings.get_dst_for_src(a.node))
            elif isinstance(a, Move):
                self.src_mv_trees.add(a.node)
                self.dst_mv_trees.add(self.diff.mappings.get_dst_for_src(a.node))
