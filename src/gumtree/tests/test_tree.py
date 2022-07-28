import ast
from src.gumtree.tests.tree_loader import get_boba_big, get_dummy_src, get_subtree_src
from src.gumtree.main.trees.default_tree import DefaultTree
from src.gumtree.main.trees.fake_tree import FakeTree
import src.gumtree.main.trees.tree_utils as tree_utils


def testSearchSubtree():
    root = get_subtree_src()
    subtree = DefaultTree("a")
    subtree.add_child(DefaultTree("b"))
    subtree.add_child(DefaultTree("c", "foo"))
    results = root.search_subtree(subtree)
    assert(2 == len(results))
    assert(results[0].is_isomorphic_to(subtree))

    results = root.search_subtree(root)
    assert(1 == len(results))
    assert(results[0].is_isomorphic_to(root))

    other_subtree = DefaultTree("a")
    other_subtree.add_child(DefaultTree("b"))
    results = root.search_subtree(other_subtree)
    assert(0 == len(results))



def testIsRoot():
    tree = DefaultTree("a")
    tree.add_child(DefaultTree("b"))
    tree.add_child(DefaultTree("c", "foo"))
    assert(tree.is_root())
    assert(not tree.children[0].is_root())
    assert(not tree.children[1].is_root())



def testInsertChild():
    tree = DefaultTree("a")
    tree.add_child(DefaultTree("b"))
    tree.add_child(DefaultTree("c", "foo"))
    print(len(tree.children))
    tree.insert_child(DefaultTree("m"), 1)
    assert("m" == tree.children[1].node_type)
    assert(tree == tree.children[1].parent)





def testChildUrl():
    root = get_dummy_src()
    assert("b" == root.get_child_from_url("0").label)
    assert("c" == root.get_child_from_url("0.0").label)
    assert("d" == root.get_child_from_url("0.1").label)
    assert("e" == root.get_child_from_url("1").label)




def testGetParents():
    tree = get_dummy_src()
    c = tree.get_child_from_url("0.0")
    assert("c" == c.label)
    parents = c.get_parents()
    assert(2 == len(parents))
    assert("b" == parents[0].label)
    assert("a" == parents[1].label)
    assert(tree == parents[len(parents) - 1])



def testGetDescendants():
    tree = get_dummy_src()
    b = tree.children[0]
    assert("b" == b.label)
    descendants = b.get_descendents()
    assert(2 == len(descendants))
    assert("c" == descendants[0].label)
    assert("d" == descendants[1].label)



def testChildManipulation():
    t1 = DefaultTree("foo")
    assert(t1.is_leaf())
    assert(t1.is_root())
    assert(-1 == t1.position_in_parent())
    assert(0 == len(t1.children))
    t2 = DefaultTree("foo")
    t1.add_child(t2)
    assert(not t1.is_leaf())
    assert(t1.is_root())
    assert(t2.is_leaf())
    assert(t1 == t2.parent)
    t3 = DefaultTree("foo")
    t3.set_parent_and_update_children(t1)
    assert(t3.is_leaf())
    assert(t1 == t3.parent)
    assert(2 == len(t1.children))
    assert(t3 == t1.children[1])
    assert(1 == t3.position_in_parent())
    assert(1 == t1.get_child_position(t3))
    t4 = DefaultTree("foo")
    t4.parent = t1
    t4.set_parent_and_update_children(t2)
    assert(t1 != t4.parent)
    assert(t2 == t4.parent)
    assert(-1 == t1.get_child_position(t4))
    assert(0 == t2.get_child_position(t4))
    children = []
    children.append(t3)
    children.append(t4)
    t2.children = children
    assert(2 == len(t2.children))
    assert(t3 in t2.children)
    assert(t4 in t2.children)
    assert(t2 == t3.parent)
    assert(t2 == t4.parent)



def testDeepCopy():
    root = get_dummy_src()
    root_cpy = root.deep_copy()
    assert(root.is_isomorphic_to(root_cpy))
    root_it = tree_utils.PreOrderIterator(root)
    for cpy in root_cpy.pre_order():
        t = next(root_it)
        assert(t != cpy)
    
    
    root_with_fake = DefaultTree("foo")
    fakeChild = FakeTree()
    root_with_fake.add_child(fakeChild)
    root_with_fake_cpy = root_with_fake.deep_copy()
    assert(root_with_fake_cpy.is_isomorphic_to(root_with_fake))
    assert(root_with_fake != root_with_fake_cpy)
    assert(root_with_fake.children[0] != root_with_fake_cpy.children[0])



def testIsomophism():
    root = get_dummy_src()
    root_cpy = get_dummy_src()
    assert(root.is_isomorphic_to(root_cpy))
    root_cpy.get_child_from_url("0.0").label = "foo"
    assert(not root.is_isomorphic_to(root_cpy))
    root.get_child_from_url("0.0").label = "foo"
    assert(root.is_isomorphic_to(root_cpy))
    root.add_child(FakeTree())
    assert(not root.is_isomorphic_to(root_cpy))
    root_cpy.add_child(FakeTree())
    assert(root.is_isomorphic_to(root_cpy))



def testIsostructure():
    root = get_dummy_src()
    root_cpy = get_dummy_src()
    assert(root.is_isostructural_to(root_cpy))
    root_cpy.get_child_from_url("0.0").label = "foo"
    assert(root.is_isostructural_to(root_cpy))
    root_cpy.get_child_from_url("0.1").node_type = "foo"
    assert(not root.is_isostructural_to(root_cpy))
    root.get_child_from_url("0.1").node_type = "foo"
    assert(root.is_isostructural_to(root_cpy))
    root.add_child(FakeTree())
    assert(not root.is_isostructural_to(root_cpy))
    root_cpy.add_child(FakeTree())
    assert(root.is_isostructural_to(root_cpy))


def testIsClone():
    tree = get_dummy_src()
    copy = tree.deep_copy()
    assert(tree.is_isomorphic_to(copy))

def testBobaTree():
    tree = get_boba_big()
    # node d
    assert(tree.get_child_from_url("0.1").num_child_boba_vars == 1)
    assert(tree.get_child_from_url("0").num_child_boba_var_nodes == 5)
    # node h
    assert(tree.get_child_from_url("2.0.0").num_child_boba_vars == 2)
    assert(tree.get_child_from_url("2.0.0").num_child_boba_var_nodes == 12) # 9 + 3
    assert(tree.get_child_from_url("2.0.0").has_boba_var(height=1))
    assert(not tree.get_child_from_url("2.0.0").has_boba_var(height=0))
    # node l
    assert(tree.get_child_from_url("2.1").num_child_boba_vars == 0)
    assert(tree.get_child_from_url("2.1").num_child_boba_var_nodes == 0) # 9 + 3
    # root
    assert(tree.num_child_boba_vars == 3)
    assert(tree.num_child_boba_var_nodes == 17)
    assert(tree.has_boba_var(height=2))
    assert(not tree.has_boba_var(height=1))
    
    

    
if __name__ == "__main__":
    testBobaTree()





