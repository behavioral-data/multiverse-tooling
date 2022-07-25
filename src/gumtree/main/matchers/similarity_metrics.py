

from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.matchers.mapping_store import MappingStore

def number_of_mapped_descendants(src: Tree, dst: Tree, mappings: MappingStore):
    dst_descendants = set(dst.get_descendents())
    mapped_descendants = 0
    
    for src_descendant in src.get_descendents():
        if mappings.is_src_mapped(src_descendant):
            dst_for_src_descendant = mappings.get_dst_for_src(src_descendant)
            if dst_for_src_descendant in dst_descendants:
                mapped_descendants += 1
    return mapped_descendants

def dice_similarity(src: Tree, dst: Tree, mappings: MappingStore):
    return dice_coefficient(number_of_mapped_descendants(src, dst, mappings),
                            len(src.get_descendents()), 
                            len(dst.get_descendents()))

def dice_coefficient(common_elements_nb: int,
                     left_elements_nb: int,
                     right_elements_nb: int):
    return 2 * common_elements_nb / (left_elements_nb + right_elements_nb)