from src.gumtree.main.trees.tree_context import TreeContext
from src.gumtree.tests.tree_loader import get_bottom_up_pair, get_gumtree_pair
from src.gumtree.main.trees.default_tree import DefaultTree
from src.gumtree.main.matchers.greedy_subtree_matcher import GreedySubtreeMatcher
from src.gumtree.main.matchers.greedy_bottomup_matcher import GreedyBottomUpMatcher

from src.gumtree.main.matchers.mapping_store import MappingStore

def testMinHeightThreshold():
    trees = get_gumtree_pair()
    t1 = trees[0].root
    t2 = trees[1].root

    matcher = GreedySubtreeMatcher()
    matcher.min_priority = 0
    ms1: MappingStore = matcher.match(t1, t2)
    assert(4 == ms1.size())
    assert(ms1.has(t1.children[1], t2.children[0]))
    assert(ms1.has(t1.get_child_from_url("1.0"), t2.get_child_from_url("0.0")))
    assert(ms1.has(t1.get_child_from_url("1.1"), t2.get_child_from_url("0.1")))
    assert(ms1.has(t1.children[2], t2.children[2]))

    matcher.min_priority = 1
    ms2: MappingStore = matcher.match(t1, t2)
    assert(3 == ms2.size())
    assert(ms1.has(t1.children[1], t2.children[0]))
    assert(ms1.has(t1.get_child_from_url("1.0"), t2.get_child_from_url("0.0")))
    assert(ms1.has(t1.get_child_from_url("1.1"), t2.get_child_from_url("0.1")))



def testMappingComparatorPosInParent():
    t1 = DefaultTree("root")
    a11 = DefaultTree("a")
    t1.add_child(a11)
    a12 = DefaultTree("a")
    t1.add_child(a12)
    a13 = DefaultTree("a")
    t1.add_child(a13)
    # root
    #     a
    #     a
    #     a

    t2 = DefaultTree("root")
    a21 = DefaultTree("a")
    t2.add_child(a21)
    a22 = DefaultTree("a")
    t2.add_child(a22)
    # root
    #     a
    #     a

    matcher = GreedySubtreeMatcher()
    matcher.min_priority = 0
    ms: MappingStore = matcher.match(t1, t2)
    assert(ms.has(a11, a21))
    assert(ms.has(a12, a22))


def testMappingComparatorPosInTree():
    t1 = DefaultTree("root")
    a11 = DefaultTree("a")
    t1.add_child(a11)
    b11 = DefaultTree("b")
    a11.add_child(b11)
    a12 = DefaultTree("a")
    t1.add_child(a12)
    b12 = DefaultTree("b")
    a12.add_child(b12)
    # root
    #     a
    #       b
    #     a
    #       b

    t2 = DefaultTree("root")
    a21 = DefaultTree("c")
    t2.add_child(a21)
    b21 = DefaultTree("b")
    a21.add_child(b21)
    a22 = DefaultTree("c")
    t2.add_child(a22)
    b22 = DefaultTree("b")
    a22.add_child(b22)
    # root
    #     c
    #       b
    #     c
    #       b

    matcher = GreedySubtreeMatcher()
    matcher.min_priority = 0
    ms: MappingStore = matcher.match(t1, t2)
    assert(ms.has(b11, b21))
    assert(ms.has(b12, b22))



def testSimAndSizeThreshold():
    trees = get_bottom_up_pair()
    t1 = trees[0]
    t2 = trees[1]
    ms = MappingStore(t1, t2)
    ms.add_mapping(t1.get_child_from_url("0.2.0"), t2.get_child_from_url("0.2.0"))
    ms.add_mapping(t1.get_child_from_url("0.2.1"), t2.get_child_from_url("0.2.1"))
    ms.add_mapping(t1.get_child_from_url("0.2.2"), t2.get_child_from_url("0.2.2"))
    ms.add_mapping(t1.get_child_from_url("0.2.3"), t2.get_child_from_url("0.2.3"))

    matcher = GreedyBottomUpMatcher()
    matcher.sim_threshold = 1.0
    matcher.size_threshold = 0

    ms1 = matcher.match(t1, t2, MappingStore.init_from_mapping_store(ms))

    assert(5 == ms1.size())
    for m in ms:
        assert(ms1.has(m[0], m[1]))
    assert(ms1.has(t1, t2))

    matcher.sim_threshold = 0.5
    matcher.size_threshold = 0

    ms2 = matcher.match(t1, t2, MappingStore.init_from_mapping_store(ms))
    assert(7 == ms2.size())
    for m in ms:
        assert(ms2.has(m[0], m[1]))
    assert(ms2.has(t1, t2))
    assert(ms2.has(t1.children[0], t2.children[0]))
    assert(ms2.has(t1.get_child_from_url("0.2"), t2.get_child_from_url("0.2")))

    matcher.sim_threshold = 0.5
    matcher.size_threshold = 10

    ms3 = matcher.match(t1, t2, MappingStore.init_from_mapping_store(ms))
    assert(9 == ms3.size())
    for m in ms:
        assert(ms3.has(m[0], m[1]))
    assert(ms3.has(t1, t2))
    assert(ms3.has(t1.children[0], t2.children[0]))
    assert(ms3.has(t1.get_child_from_url("0.0"), t2.get_child_from_url("0.0")))
    assert(ms3.has(t1.get_child_from_url("0.1"), t2.get_child_from_url("0.1")))
    assert(ms3.has(t1.get_child_from_url("0.2"), t2.get_child_from_url("0.2")))


if __name__ == "__main__":
    testMinHeightThreshold()
    testMappingComparatorPosInTree()
    testMappingComparatorPosInParent() 
    testSimAndSizeThreshold()
    