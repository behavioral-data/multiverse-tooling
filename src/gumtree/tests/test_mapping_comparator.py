from src.gumtree.main.trees.default_tree import DefaultTree
from src.gumtree.main.matchers.mapping_store import MappingStore
import src.gumtree.main.matchers.mapping_comparators as mapping_comparators

def test_twin_mappings():
    src = DefaultTree(node_type="foo")
    src.add_child(DefaultTree(node_type="foo"))
    # src.children[0].setPos(0)
    # src.children[0].setLength(3)
    src.add_child(DefaultTree(node_type="foo"))
    # src.children[1].setPos(3)
    # src.children[1].setLength(3)
    dst = src.deep_copy()
    ms =  MappingStore(src, dst)
    ms.add_mapping(src.children[0], dst.children[1])
    ms.add_mapping(src.children[1], dst.children[0])
    mappings = list(ms.as_set())
    sc = mapping_comparators.SiblingsSimilarityMappingComparator(ms)
    assert(0 == sc.compare(mappings[0], mappings[1]))
    pc = mapping_comparators.ParentsSimilarityMappingComparator()
    assert(0 == pc.compare(mappings[0], mappings[1]))
    ppc =  mapping_comparators.PositionInParentsSimilarityMappingComparator()
    assert(0 == ppc.compare(mappings[0], mappings[1]))
    # Not implemented
    # tc = mapping_comparators.TextualPositionDistanceMappingComparator()
    # assert(0, tc.compare(mappings[0), mappings[1)))
    
    ac = mapping_comparators.AbsolutePositionDistanceMappingComparator()
    assert(0 == ac.compare(mappings[0], mappings[1]))
    
if __name__ == '__main__':
    test_twin_mappings()