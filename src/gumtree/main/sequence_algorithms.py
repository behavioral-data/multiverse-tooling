from typing import List
from src.gumtree.main.trees.tree import Tree
    
def longest_common_subsequence_with_type(s0: List[Tree], s1: List[Tree]) -> List[List[int]]:
    lengths = [[0] * (len(s1) + 1) for _ in range(len(s0)+1)]
    for i in range(len(s0)):
        for j in range(len(s1)):
            if s0[i].has_same_type(s1[j]):
                lengths[i + 1][j + 1] = lengths[i][j] + 1
            else:
                lengths[i + 1][j+ 1] = max(lengths[i + 1][j], lengths[i][j+1])
    
    return extract_indexes(lengths, len(s0), len(s1))


def extract_indexes(lengths: List[List[int]], length1, length2):
    indexes = []
    x = length1
    y = length2
    while x != 0 and y != 0:
        if lengths[x][y] == lengths[x-1][y]:
            x -= 1
        elif lengths[x][y] == lengths[x][y -1]:
            y -= 1
        else:
            indexes.append([x-1, y-1])
            y -= 1
            x -= 1
    indexes.reverse()
    return indexes