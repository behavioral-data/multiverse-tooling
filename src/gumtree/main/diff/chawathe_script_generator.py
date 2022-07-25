from typing import Set, Dict, List, Tuple
from src.gumtree.main.diff.edit_script import EditScript, EditScriptGenerator
from src.gumtree.main.matchers.mapping_store import MappingStore
from src.gumtree.main.trees.tree_utils import PreOrderIterator, preorder, breadth_first

from src.gumtree.main.trees.fake_tree import FakeTree

from src.gumtree.main.diff.actions.insert import Insert
from src.gumtree.main.diff.actions.update import Update
from src.gumtree.main.diff.actions.move import Move
from src.gumtree.main.diff.actions.delete import Delete

from src.gumtree.main.trees.tree import Tree

class ChawatheScriptGenerator(EditScriptGenerator):
    
    def __init__(self, ms: MappingStore):
        self.orig_src: Tree = ms.src
        self.cpy_src: Tree = self.orig_src.deep_copy()
        self.orig_dst: Tree = ms.dst
        self.orig_mappings = ms
        
        self.orig_to_copy: Dict[Tree, Tree] = {}
        self.copy_to_orig: Dict[Tree, Tree] = {}
        
        cpy_tree_iterator = PreOrderIterator(self.cpy_src)
        for orig_tree in preorder(self.orig_src):
            cpy_tree = next(cpy_tree_iterator)
            self.orig_to_copy[orig_tree] = cpy_tree
            self.copy_to_orig[cpy_tree] = orig_tree
        self.cpy_mappings = MappingStore(ms.src, ms.dst)
        
        for mapping in self.orig_mappings:
            self.cpy_mappings.add_mapping(self.orig_to_copy[mapping[0]], mapping[1])
            
        self.dst_in_order: Set[Tree] = None
        self.src_in_order: Set[Tree] = None
        self.actions: EditScript = None
    
    @staticmethod
    def compute_actions(ms: MappingStore):
        script_generator = ChawatheScriptGenerator(ms)
        script_generator.generate()
        return script_generator.actions
        
    def generate(self) -> EditScript:
        src_fake_root = FakeTree(self.cpy_src)
        dst_fake_root = FakeTree(self.orig_dst)
        self.cpy_src.parent = src_fake_root
        self.orig_dst = dst_fake_root
        
        self.actions = EditScript()
        self.dst_in_order = set()
        self.src_in_order = set()
        
        self.cpy_mappings.add_mapping(src_fake_root, dst_fake_root)
        bfs_dst: List[Tree] = breadth_first(self.orig_dst)
        for x in bfs_dst:
            y: Tree = x.parent
            z: Tree = self.cpy_mappings.get_src_for_dst(y)
            if not self.cpy_mappings.is_dst_mapped(x):
                k = self.find_pos(x)
                w = FakeTree()
                ins = Insert(x, self.copy_to_orig[z], k)
                self.actions.add(ins)
                self.copy_to_orig[w] = k
                self.cpy_mappings.add_mapping(w, x)
                z.insert_child(w, k)
            else:
                w = self.cpy_mappings.get_src_for_dst(x)
                if x != self.orig_dst:
                    v = w.parent
                    if not (w.label == x.label):
                        self.actions.add(Update(self.copy_to_orig[w], x.label))
                        w.label = x.label
                    
                    if z != v:
                        k = self.find_pos(x)
                        mv = Move(self.copy_to_orig[w], self.copy_to_orig[z], k)
                        self.actions.add(mv)
                        oldk = w.position_in_parent()
                        w.parent.children.pop(oldk)
                        z.insert_child(w, k)
            self.src_in_order.add(w)
            self.dst_in_order.add(x)
            self.align_children(w, x)
        
        for w in self.cpy_src.post_order():
            if not self.cpy_mappings.is_src_mapped(w):
                self.actions.add(Delete(self.copy_to_orig[w]))
        
        return self.actions
    
    def align_children(self, w: Tree, x: Tree):
        self.src_in_order = self.src_in_order - set(w.children)
        self.dst_in_order = self.dst_in_order - set(x.children)
        
        s1: List[Tree] = []
        for c in w.children:
            if self.cpy_mappings.is_src_mapped(c):
                if self.cpy_mappings.get_dst_for_src(x) in x.children:
                    s1.append(c)
        
        s2: List[Tree] = []
        for c in x.children:
            if self.cpy_mappings.is_dst_mapped(c):
                if self.cpy_mappings.get_src_for_dst(c) in w.children:
                    s2.append(c)

        lcs = self.lcs(s1, s2)
        for m in lcs:
            self.src_in_order.add(m[0])
            self.dst_in_order.add(m[1])
            
        for b in s2:
            for a in s1:
                if self.cpy_mappings.has(a, b):
                    if (a, b) not in lcs:
                        a.parent.children.remove(a)
                        k = self.find_pos(b)
                        mv = Move(self.copy_to_orig[a], self.copy_to_orig[w], k)
                        self.actions.add(mv)
                        w.children.insert(k, a)
                        a.parent = w
                        self.src_in_order.add(a)
                        self.dst_in_order.add(b)
            
                        
        
    def find_pos(self, x: Tree) -> int:
        y = x.parent
        siblings: List[Tree] = y.children
        
        for c in siblings:
            if c in self.dst_in_order:
                if c == x:
                    return 0
            else:
                break
        xpos = x.position_in_parent()
        v: Tree = None
        for i in range(xpos):
            c = siblings[i]
            if c in self.dst_in_order:
                v = c
        
        if v is None:
            return 0
        
        u: Tree = self.cpy_mappings.get_src_for_dst(v)
        upos = u.position_in_parent()
        return upos + 1
            
    
    def lcs(self, x: List[Tree], y: List[Tree]) -> List[Tuple[Tree, Tree]]:
        m = len(x)
        n = len(y)
        
        ret: List[Tuple[Tree, Tree]] = []
        opt = [[0]*(n+1) for _ in range(m+1)]
        for i in range(m-1, -1, -1):
            for j in range(n-1, -1, -1):
                if self.cpy_mappings.get_src_for_dst(y[j]) == x[i]:
                    opt[i][j] = opt[i + 1][j + 1] + 1
                else:
                    opt[i][j] = max(opt[i + 1][j], opt[i][j + 1])
        
        i = 0
        j = 0
        while i < m and j < n:
            if self.cpy_mappings.get_dst_for_src(y[j]) == x[i]:
                ret.append((x[i], y[j]))
                i += 1
                j += 1
            elif opt[i + 1][j] >= opt[i][j + 1]:
                i += 1
            else:
                j += 1
        
        return ret