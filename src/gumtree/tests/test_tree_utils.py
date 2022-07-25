from typing import Iterable, List
from src.gumtree.tests.tree_loader import get_dummy_src, get_dummy_dst, get_dummy_big
from src.gumtree.main.trees.tree_visitor import TreeMetricComputer
from src.gumtree.main.trees.default_tree import DefaultTree
import src.gumtree.main.trees.tree_utils as tree_utils
from src.gumtree.main.trees.tree_utils import TreeIterator, HNIterator

from src.gumtree.main.trees.tree import Tree

def testPostOrderNumbering():
    root = get_dummy_src()    
    assert(4 == root.tree_metrics.position)
    assert(2 == root.children[0].tree_metrics.position)
    assert(0 == root.get_child_from_url("0.0").tree_metrics.position)
    assert(1 == root.get_child_from_url("0.1").tree_metrics.position)
    assert(3 == root.children[1].tree_metrics.position)


def testDepth():
    root = get_dummy_src()
    print(root.to_tree_string())
    assert(0 == root.tree_metrics.depth)
    assert(1 == root.children[0].tree_metrics.depth)
    assert(2 == root.get_child_from_url("0.0").tree_metrics.depth)
    assert(2 == root.get_child_from_url("0.1").tree_metrics.depth)
    assert(1 == root.children[1].tree_metrics.depth)



def testSize():
    root = get_dummy_src()
    print(root.to_tree_string())
    assert(5 == root.tree_metrics.size)
    assert(3 == root.children[0].tree_metrics.size)
    assert(1 == root.get_child_from_url("0.0").tree_metrics.size)
    assert(1 == root.get_child_from_url("0.1").tree_metrics.size)
    assert(1 == root.children[1].tree_metrics.size)


def testHashValue():
    t0 = get_dummy_src()
    t1 = get_dummy_src()
    t2 = t1.deep_copy()
    t2.label = "foo"
    t3 = t2.deep_copy()
    t3.add_child(DefaultTree("foo"))
    # print(f"T1:\n{t1.to_tree_string()}")
    # print(f"T2:\n{t2.to_tree_string()}")
    # print(f"T3:\n{t3.to_tree_string()}")
    assert(t0.tree_metrics.hashcode == t1.tree_metrics.hashcode)
    assert(t0.tree_metrics.hashcode != t2.tree_metrics.hashcode)
    assert(t0.tree_metrics.hashcode != t3.tree_metrics.hashcode)
    assert(t0.tree_metrics.structure_hash == t1.tree_metrics.structure_hash)
    assert(t0.tree_metrics.structure_hash == t2.tree_metrics.structure_hash)
    assert(t0.tree_metrics.structure_hash != t3.tree_metrics.structure_hash)



def testHeight():
    root = get_dummy_src()
    assert(2 == root.tree_metrics.height) # depth of a
    assert(1 == root.children[0].tree_metrics.height) # depth of b
    assert(0 == root.get_child_from_url("0.0").tree_metrics.height) # depth of c
    assert(0 == root.get_child_from_url("0.1").tree_metrics.height) # depth of d
    assert(0 == root.children[1].tree_metrics.height) # depth of e



def testPostOrder():
    src = get_dummy_src()
    lst = tree_utils.post_order(src)
    it = tree_utils.PostOrderIterator(src)
    compare_list_iterator(lst, it)




def testPostOrder2():
    dst = get_dummy_dst()
    lst = tree_utils.post_order(dst)
    it = tree_utils.PostOrderIterator(dst)
    compare_list_iterator(lst, it)



def testPostOrder3():
    big = get_dummy_big()
    lst = tree_utils.post_order(big)
    it = tree_utils.PostOrderIterator(big)
    compare_list_iterator(lst, it)




def testBfsList():
    src = get_dummy_src()
    dst = get_dummy_dst()
    big = get_dummy_big()
    compare_list_iterator_str(HNIterator(tree_utils.breadth_first(src)), ["a", "b", "e", "c", "d"])
    compare_list_iterator_str(HNIterator(tree_utils.breadth_first(dst)), ["a", "f", "i", "b", "j", "c", "d", "h"])
    compare_list_iterator_str(HNIterator(tree_utils.breadth_first(big)), ["a", "b", "e", "f", "c",
            "d", "g", "l", "h", "m", "i", "j", "k"])



def testPreOrderList():
    src = get_dummy_src()
    dst = get_dummy_dst()
    big = get_dummy_big()
    compare_list_iterator_str(tree_utils.PreOrderIterator(src), ["a", "b", "c", "d", "e"])
    compare_list_iterator_str(tree_utils.PreOrderIterator(dst), ["a", "f", "b", "c", "d", "h", "i", "j"])
    compare_list_iterator_str(tree_utils.PreOrderIterator(big), ["a", "b", "c", "d", "e",
            "f", "g", "h", "i", "j", "k", "l", "m"])

    
    
def compare_list_iterator(lst: List[Tree], it: TreeIterator):
    for i in lst:
        assert i == next(it) 
    assert not it.has_next()
    
def compare_list_iterator_str(it: TreeIterator, expected: List[str]):
    for e in expected:
        tree = next(it)
        assert e == tree.label
    assert not it.has_next()
    

if __name__ == "__main__":
    testDepth()
    testSize()
    testPostOrderNumbering()
    testHashValue()
    testHeight()
    testPostOrder()
    testPostOrder2()
    testPostOrder3()
    testBfsList()
    testPreOrderList()