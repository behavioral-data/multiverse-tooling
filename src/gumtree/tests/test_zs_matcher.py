
from src.gumtree.tests.tree_loader import get_zs_custom_pair, get_zs_slide_pair
from src.gumtree.main.matchers.zs_matcher import ZsMatcher
from src.gumtree.main.matchers.mapping_store import MappingStore

def testWithCustomExample():
    trees = get_zs_custom_pair()
    src = trees[0].root
    dst = trees[1].root
    mappings = ZsMatcher().match(src, dst, MappingStore(src, dst))
    assert(6 == mappings.size())
    assert(mappings.has(src, dst.children[0]))
    assert(mappings.has(src.children[0], dst.get_child_from_url("0.0")))
    assert(mappings.has(src.children[1], dst.get_child_from_url("0.1")))
    assert(mappings.has(src.get_child_from_url("1.0"), dst.get_child_from_url("0.1.0")))
    assert(mappings.has(src.get_child_from_url("1.2"), dst.get_child_from_url("0.1.2"))) # DefaultTree: 0 (r1) and DefaultTree: 0 (f)
    assert(mappings.has(src.get_child_from_url("1.3"), dst.get_child_from_url("0.1.3"))) # DefaultTree: 0 (r2)  



def testWithSlideExample():
    trees = get_zs_slide_pair()
    src = trees[0].root
    dst = trees[1].root
    mappings = ZsMatcher().match(src, dst, MappingStore(src, dst))
    assert(5 == mappings.size())
    assert(mappings.has(src, dst))
    assert(mappings.has(src.get_child_from_url("0.0"), dst.children[0])) # DefaultTree: 0 (2) and DefaultTree: 0 (2)
    assert(mappings.has(src.get_child_from_url("0.0.0"), dst.get_child_from_url("0.0"))) # DefaultTree: 0 (1) and DefaultTree: 0 (1)
    assert(mappings.has(src.get_child_from_url("0.1"), dst.get_child_from_url("1.0"))) # DefaultTree: 0 (3) and DefaultTree: 0 (3)
    assert(mappings.has(src.get_child_from_url("0.2"), dst.children[2])) # DefaultTree: 1 (4) and DefaultTree: 0 (5) 

if __name__ == "__main__":
    testWithCustomExample()
    testWithSlideExample()