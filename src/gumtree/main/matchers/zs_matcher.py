from typing import List
from collections import deque
from src.gumtree.main.matchers.mapping_store import MappingStore
from src.gumtree.main.matchers.matcher import Matcher
from src.gumtree.main.trees.tree import Tree
from strsimpy.qgram import QGram


class QgramPadded(QGram):
    DEFAULT_START_PADDING = '#'
    DEFAULT_END_PADDING = '#'
    
    def __init__(self, k=3):
        super().__init__(k)
        self.start_padding = self.DEFAULT_START_PADDING * (k - 1)
        self.end_padding = self.DEFAULT_END_PADDING * (k - 1)
        
    def compare(self, s0, s1): # simulate string metrics compare with padding
        s0 = self.start_padding + s0 + self.end_padding
        s1 = self.start_padding + s1 + self.end_padding
        if len(s0) == 0 and len(s1) == 0:
            return 1.0
        elif len(s0) == 0 or len(s1) == 0:
            return 0.0
            
        return 1.0 - (self.distance(s0, s1) / (len(s0) + len(s1)))

class ZsTree:
    def __init__(self, tree: Tree):
        self.node_count = tree.tree_metrics.size
        self.leaf_count = 0
        self.llds: List[int] = [0] * self.node_count
        self.labels: List[Tree] = [None] * self.node_count
        self.kr = None
        
        idx = 1
        tmp_data ={}
        for n in tree.post_order():
            tmp_data[n] = idx
            self.set_itree(idx, n)
            self.set_lld(idx, tmp_data[ZsMatcher.get_first_leaf(n)])
            if n.is_leaf():
                self.leaf_count += 1
            idx += 1
            
        self.set_key_roots()
        
    def set_itree(self, i: int, tree: Tree):
        self.labels[i - 1] = tree
        if self.node_count < i:
            self.node_count = i
            
    def set_lld(self, i: int, lld: int):
        self.llds[i - 1] = lld - 1
        if self.node_count < 1:
            self.node_count = i
            
    def is_leaf(self, i: int):
        return self.llds(i) == i
    
    def lld(self, i: int) -> int:
        return self.llds[i - 1] + 1
    
    def tree(self, i: int) -> Tree:
        return self.labels[i - 1]
    
    def set_key_roots(self):
        self.kr = [0] * (self.leaf_count + 1)
        visited = [False] * (self.node_count + 1)
        k = len(self.kr) - 1
        for i in range(self.node_count, 0, -1):
            if not visited[self.lld(i)]:
                self.kr[k] = i
                visited[self.lld(i)] = True
                k -= 1
        
        
class ZsMatcher(Matcher):
    
    def __init__(self):
        self.mappings: MappingStore = None
        self.zs_src: ZsTree = None
        self.zs_dst: ZsTree = None
        self.tree_dist: List[List[float]] = None
        self.forest_dist: List[List[float]] = None
    
    def configure(self):
        pass
    
    @staticmethod
    def get_first_leaf(t: Tree):
        current = t 
        while not current.is_leaf():
            current = current.children[0]
        return current
    
    def match(self, src: Tree, dst: Tree, mappings: MappingStore) -> MappingStore:
        self.zs_src = ZsTree(src)
        self.zs_dst = ZsTree(dst)
        self.mappings = mappings
        self.match_help()
        return self.mappings
    
    def compute_tree_dist(self) -> List[List[float]]:
        self.tree_dist = [[0] * (self.zs_dst.node_count + 1) for _ in range(self.zs_src.node_count + 1)]
        self.forest_dist = [[0] * (self.zs_dst.node_count + 1) for _ in range(self.zs_src.node_count + 1)]
        
        for i in range(1, len(self.zs_src.kr)):
            for j in range(1, len(self.zs_dst.kr)):
                self.calc_forest_dist(self.zs_src.kr[i], self.zs_dst.kr[j])
        return self.tree_dist

    def calc_forest_dist(self, i: int, j: int):
        self.forest_dist[self.zs_src.lld(i) - 1][self.zs_dst.lld(j) - 1] = 0
        for di in range(self.zs_src.lld(i), i+1):
            cost_del = self.get_deletion_cost(self.zs_src.tree(di))
            self.forest_dist[di][self.zs_dst.lld(j) - 1] = self.forest_dist[di - 1][self.zs_dst.lld(j) - 1] + cost_del
            for dj in range(self.zs_dst.lld(j), j+1):
                cost_inds = self.get_insertion_cost(self.zs_dst.tree(dj))
                self.forest_dist[self.zs_src.lld(i) - 1][dj] = self.forest_dist[self.zs_src.lld(i) - 1][dj - 1] + cost_inds

                if (self.zs_src.lld(di) == self.zs_src.lld(i)) and (self.zs_dst.lld(dj) == self.zs_dst.lld(j)):
                    cost_upd = self.get_update_cost(self.zs_src.tree(di), self.zs_dst.tree(dj))
                    self.forest_dist[di][dj] = min(
                        min(self.forest_dist[di - 1][dj] + cost_del, self.forest_dist[di][dj - 1] + cost_inds),
                            self.forest_dist[di - 1][dj - 1] + cost_upd)
                    self.tree_dist[di][dj] = self.forest_dist[di][dj]
                else:
                    self.forest_dist[di][dj] = min(
                        min(self.forest_dist[di - 1][dj] + cost_del, self.forest_dist[di][dj - 1] + cost_inds),
                            self.forest_dist[self.zs_src.lld(di) - 1][self.zs_dst.lld(dj) - 1] + self.tree_dist[di][dj])
            
            
    def get_deletion_cost(self, n: Tree):
        return 1.0
    
    def get_insertion_cost(self, n: Tree):
        return 1.0
        
    def get_update_cost(self, n1: Tree, n2: Tree):
        if n1.node_type == n2.node_type:
            if n1.label == "" or n2.label == "":
                return 1.0
            else:
                return 1.0 - QgramPadded(k=3).compare(n1.label, n2.label)
        else:
            return float('inf')
        
    def match_help(self):
        self.compute_tree_dist()
        root_node_pair = True
        tree_pairs: deque[List[int]] = deque()
        tree_pairs.append([self.zs_src.node_count, self.zs_dst.node_count])
        while not len(tree_pairs) == 0:
            tree_pair = tree_pairs.popleft()
            last_row = tree_pair[0]
            last_col = tree_pair[1]
            if not root_node_pair:
                self.calc_forest_dist(last_row, last_col)
            root_node_pair = False
            
            first_row = self.zs_src.lld(last_row) - 1
            first_col = self.zs_dst.lld(last_col) - 1
            
            row = last_row
            col = last_col
            
            while row > first_row or col > first_col:
                if (row > first_row) and (self.forest_dist[row - 1][col] + 1 == self.forest_dist[row][col]):
                    row -= 1
                elif (col >  first_col) and (self.forest_dist[row][col - 1] + 1 == self.forest_dist[row][col]):
                    # node with postorderID col is inserted into ted2
                    col -= 1
                else:
                    # node with postorderID row in ted1 is renamed to node col
                    # in ted2
                    if ((self.zs_src.lld(row) - 1 == self.zs_src.lld(last_row) - 1)
                            and (self.zs_dst.lld(col) - 1 == self.zs_dst.lld(last_col) - 1)):
                        # if both subforests are trees, map nodes
                        t_src = self.zs_src.tree(row);
                        t_dst = self.zs_dst.tree(col);
                        if (t_src.node_type == t_dst.node_type):
                            self.mappings.add_mapping(t_src, t_dst);
                        else:
                            raise Exception("Should not map incompatible nodes.")
                        row -= 1
                        col -= 1
                    else:
                        # pop subtree pair
                        tree_pairs.appendleft([row, col])
                        # continue with forest to the left of the popped
                        # subtree pair

                        row = self.zs_src.lld(row) - 1
                        col = self.zs_dst.lld(col) - 1 