
from src.gumtree.main.diff.simplified_chawathe_script_generator import SimplifiedChawatheScriptGenerator
from src.gumtree.main.diff.actions.insert import Insert
from src.gumtree.main.diff.actions.move import Move
from src.gumtree.main.diff.actions.tree_addition import TreeInsert
from src.gumtree.main.diff.actions.tree_delete import TreeDelete
from src.gumtree.main.diff.actions.update import Update
from src.gumtree.main.diff.chawathe_script_generator import ChawatheScriptGenerator
from src.gumtree.tests.tree_loader import get_action_pair, get_zs_custom_pair

from src.gumtree.main.matchers.mapping_store import MappingStore
from src.gumtree.main.trees.default_tree import DefaultTree

from src.gumtree.main.diff.actions.delete import Delete

def testWithActionExample():
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
    assert(9 == len(actions))

    a = actions.get(0)
    assert(isinstance(a, Insert))
    i: Insert = a
    assert("h" == i.node.label)
    assert("a" == i.parent.label)
    assert(2 == i.pos)

    a = actions.get(1)
    assert(isinstance(a, TreeInsert))
    ti: TreeInsert = a
    assert("x" == ti.node.label)
    assert("a" == ti.parent.label)
    assert(3 == ti.pos)

    a = actions.get(2)
    assert(isinstance(a, Move))
    m: Move = a
    assert("e" == m.node.label)
    assert("h" == m.parent.label)
    assert(0 == m.pos)

    a = actions.get(3)
    assert(isinstance(a, Insert))
    i2: Insert = a
    assert("u" == i2.node.label)
    assert("j" == i2.parent.label)
    assert(0 == i2.pos)

    a = actions.get(4)
    assert(isinstance(a, Update))
    u: Update = a
    assert("f" == u.node.label)
    assert("y" == u.value)

    a = actions.get(5)
    assert(isinstance(a, Insert))
    i3: Insert = a
    assert("v" == i3.node.label)
    assert("u" == i3.parent.label)
    assert(0 == i3.pos)

    a = actions.get(6)
    assert(isinstance(a, Move))
    m2: Move = a
    assert("k" == m2.node.label)
    assert("v" == m2.parent.label)
    assert(0 == m.pos)

    a = actions.get(7)
    assert(isinstance(a, TreeDelete))
    td: TreeDelete = a
    assert("g" == td.node.label)

    a = actions.get(8)
    assert(isinstance(a, Delete))
    d: Delete = a
    assert("i" == d.node.label)


def testWithUnmappedRoot():
    src = DefaultTree("foo", "")
    dst = DefaultTree("bar", "")
    ms = MappingStore(src, dst)
    actions = SimplifiedChawatheScriptGenerator.compute_actions(ms)
    assert(2 == len(actions))


# def testWithActionExampleNoMove():
#     trees = get_action_pair()
#     src = trees[0].root
#     dst = trees[1].root
#     ms = MappingStore(src, dst)
#     ms.add_mapping(src, dst)
#     ms.add_mapping(src.children[1], dst.children[0])
#     ms.add_mapping(src.children[1].children[0], dst.children[0].children[0])
#     ms.add_mapping(src.children[1].children[1], dst.children[0].children[1])
#     ms.add_mapping(src.children[0], dst.children[1].children[0])
#     ms.add_mapping(src.children[0].children[0], dst.children[1].children[0].children[0])
#     ms.add_mapping(src.children[4], dst.children[3])
#     ms.add_mapping(src.children[4].children[0], dst.children[3].children[0].children[0].children[0])

#     actions = InsertDeleteChawatheScriptGenerator.compute_actions(ms)

#     assert(1 == len(actions))


def testWithZsCustomExample():
    trees = get_zs_custom_pair()
    src = trees[0].root
    dst = trees[1].root
    ms = MappingStore(src, dst)
    ms.add_mapping(src, dst.children[0])
    ms.add_mapping(src.children[0], dst.get_child_from_url("0.0"))
    ms.add_mapping(src.children[1], dst.get_child_from_url("0.1"))
    ms.add_mapping(src.get_child_from_url("1.0"), dst.get_child_from_url("0.1.0"))
    ms.add_mapping(src.get_child_from_url("1.2"), dst.get_child_from_url("0.1.2"))
    ms.add_mapping(src.get_child_from_url("1.3"), dst.get_child_from_url("0.1.3"))

    actions = ChawatheScriptGenerator.compute_actions(ms)
    assert(5 == len(actions))
    assert(all(item in actions for item in [
            Insert(dst, None, 0),
            Move(src, dst, 0),
            Insert(dst.get_child_from_url("0.1.1"), src.get_child_from_url("1"), 1),
            Update(src.get_child_from_url("1.3"), "r2"),
            Delete(src.get_child_from_url("1.1"))]
    ))

    actions = SimplifiedChawatheScriptGenerator.compute_actions(ms)
    assert(5 == len(actions))
    assert(all(item in actions for item in [
            Insert(dst, None, 0),
            Move(src, dst, 0),
            Insert(dst.get_child_from_url("0.1.1"), src.get_child_from_url("1"), 1),
            Update(src.get_child_from_url("1.3"), "r2"),
            Delete(src.get_child_from_url("1.1"))]
    ))



    # actions = InsertDeleteChawatheScriptGenerator.compute_actions(ms)
    # assert(7 == len(actions))
    # assert(all(item in actions for item in [
    #         Insert(dst, None, 0),
    #         TreeDelete(src),
    #         TreeInsert(dst.children[0], dst, 0),
    #         Insert(dst.get_child_from_url("0.1.1"), src.get_child_from_url("1"), 1),
    #         Delete(src.get_child_from_url("1.1")),
    #         Delete(src.get_child_from_url("1.3")),
    #         Insert(dst.get_child_from_url("0.1.1"), src.children[1], 1)]
    # ))


def testAlignChildren():
    t1 = DefaultTree("root")
    a1 = DefaultTree("a")
    t1.add_child(a1)
    b1 = DefaultTree("b")
    t1.add_child(b1)
    # root [0,0]
    #     a [0,0]
    #     b [0,0]

    t2 = DefaultTree("root")
    b2 = DefaultTree("b")
    t2.add_child(b2)
    a2 = DefaultTree("a")
    t2.add_child(a2)
    # root [0,0]
    #     b [0,0]
    #     a [0,0]

    mp = MappingStore(t1, t2)
    mp.add_mapping(t1, t2)
    mp.add_mapping(a1, a2)
    mp.add_mapping(b1, b2)

    actions =  ChawatheScriptGenerator.compute_actions(mp)

    # one action to move a to pos 1 of the children of root and one action to move b to position 0
    assert(1 == len(actions))

