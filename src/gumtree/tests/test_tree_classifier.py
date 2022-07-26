from src.gumtree.main.diff.actions.tree_classifier import TreeClassifier
from src.gumtree.tests.tree_loader import get_action_pair

from src.gumtree.main.matchers.mapping_store import MappingStore

from src.gumtree.main.diff.diff import Diff

from src.gumtree.main.diff.simplified_chawathe_script_generator import SimplifiedChawatheScriptGenerator

def testAllNodesClassifier():
    trees = get_action_pair()
    src = trees[0].root
    dst = trees[1].root
    ms = MappingStore(src, dst)
    ms.add_mapping(src, dst)
    ms.add_mapping(src.children[1], dst.children[0])
    ms.add_mapping(src.get_child_from_url("1.0"), dst.get_child_from_url("0.0"))
    ms.add_mapping(src.get_child_from_url("1.1"), dst.get_child_from_url("0.1"))
    ms.add_mapping(src.children[0], dst.children[1].children[0])
    ms.add_mapping(src.get_child_from_url("0.0"), dst.get_child_from_url("1.0.0"))
    ms.add_mapping(src.children[4], dst.children[3])
    ms.add_mapping(src.get_child_from_url("4.0"), dst.get_child_from_url("3.0.0.0"))
    actions = SimplifiedChawatheScriptGenerator.compute_actions(ms)
    diff = Diff(trees[0], trees[0], ms, actions)
    c: TreeClassifier = diff.createAllNodeClassifier()
    assert(len(c.get_updated_srcs()) == 1)
    assert(src.get_child_from_url("0.0") in c.get_updated_srcs())
    assert(len(c.get_deleted_srcs()) == 3)
    assert(all(item in c.get_deleted_srcs() 
               for item in [src.get_child_from_url("2"), src.get_child_from_url("2.0"), src.get_child_from_url("3")]))
    assert(len(c.get_moved_srcs()) == 3)
    assert(all(item in c.get_moved_srcs() 
               for item in [src.get_child_from_url("0"), src.get_child_from_url("0.0"), src.get_child_from_url("4.0")]))
    assert(len(c.get_inserted_dsts()) == 5)
    assert(all( item in c.get_inserted_dsts() for item in [dst.get_child_from_url("2"),
            dst.get_child_from_url("3.0"), dst.get_child_from_url("1"), dst.get_child_from_url("2.0"), dst.get_child_from_url("3.0.0")]))
    assert(len(c.get_updated_dsts()) == 1)
    assert(dst.get_child_from_url("1.0.0") in c.get_updated_dsts())
    assert(len(c.get_moved_dsts()) == 3)
    assert(all(item in c.get_moved_dsts() for item in
            [dst.get_child_from_url("1.0"), dst.get_child_from_url("1.0.0"), dst.get_child_from_url("3.0.0.0")]))

def testOnlyRootsClassifier():
    trees = get_action_pair()
    src = trees[0].root
    dst = trees[1].root
    ms = MappingStore(src, dst)
    ms.add_mapping(src, dst)
    ms.add_mapping(src.children[1], dst.children[0])
    ms.add_mapping(src.get_child_from_url("1.0"), dst.get_child_from_url("0.0"))
    ms.add_mapping(src.get_child_from_url("1.1"), dst.get_child_from_url("0.1"))
    ms.add_mapping(src.children[0], dst.children[1].children[0])
    ms.add_mapping(src.get_child_from_url("0.0"), dst.get_child_from_url("1.0.0"))
    ms.add_mapping(src.children[4], dst.children[3])
    ms.add_mapping(src.get_child_from_url("4.0"), dst.get_child_from_url("3.0.0.0"))
    actions = SimplifiedChawatheScriptGenerator.compute_actions(ms)
    diff = Diff(trees[0], trees[1], ms, actions)
    c: TreeClassifier = diff.createRootNodesClassifier()
    assert(len(c.get_updated_srcs()) == 1)
    assert(src.get_child_from_url("0.0") in c.get_updated_srcs())
    assert(len(c.get_deleted_srcs()) == 2)
    assert(src.get_child_from_url("2") in c.get_deleted_srcs() and src.get_child_from_url("3") in c.get_deleted_srcs())
    assert(len(c.get_moved_srcs()) == 2)
    assert(src.get_child_from_url("0") in c.get_moved_srcs() and src.get_child_from_url("4.0") in c.get_moved_srcs())
    assert(len(c.get_inserted_dsts()) == 4)
    assert(all(item in c.get_inserted_dsts() for item in [dst.get_child_from_url("2"),
            dst.get_child_from_url("3.0"), dst.get_child_from_url("1"), dst.get_child_from_url("3.0.0")]))
    assert(len(c.get_updated_dsts()) == 1)
    assert(dst.get_child_from_url("1.0.0") in c.get_updated_dsts())
    assert(len(c.get_moved_dsts()) == 2)
    assert(dst.get_child_from_url("1.0") in c.get_moved_dsts() and dst.get_child_from_url("3.0.0.0") in c.get_moved_dsts())

if __name__ == "__main__":
    testAllNodesClassifier()
    testOnlyRootsClassifier()