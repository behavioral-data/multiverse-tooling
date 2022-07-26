from re import X
from typing import Tuple
from src.gumtree.main.trees.tree_context import TreeContext
from src.gumtree.main.trees.tree import Tree


def gum_tree_v0() -> TreeContext:
    tc = TreeContext()
    a = tc.create_tree("0", label="a")
    tc.root = a
    
    e = tc.create_tree("0", label="e")
    e.set_parent_and_update_children(a)
    
    f = tc.create_tree("0", label="f")
    f.set_parent_and_update_children(e)
    
    b = tc.create_tree("0", label="b")
    b.set_parent_and_update_children(a)
    
    c = tc.create_tree("0", label="c")
    c.set_parent_and_update_children(b)
    
    d = tc.create_tree("0", label="d")
    d.set_parent_and_update_children(b)
    

    g = tc.create_tree("0", label="g")
    g.set_parent_and_update_children(a)
    return tc

def gum_tree_v1() -> TreeContext:
    tc = TreeContext()
    a = tc.create_tree("0", label="z")
    tc.root = a
    
    b = tc.create_tree("0", label="b")
    b.set_parent_and_update_children(a)
    
    c = tc.create_tree("0", label="c")
    c.set_parent_and_update_children(b)
    
    d = tc.create_tree("0", label="d")
    d.set_parent_and_update_children(b)
    
    h = tc.create_tree("1", label="h")
    h.set_parent_and_update_children(a)
    
    e = tc.create_tree("0", label="e")
    e.set_parent_and_update_children(h)
    
    y = tc.create_tree("0", label="y")
    y.set_parent_and_update_children(e)
    
    g = tc.create_tree("0", label="g")
    g.set_parent_and_update_children(a)
    return tc

def bottom_up_v0() -> TreeContext:
    tc = TreeContext()
    td = tc.create_tree("td")
    tc.root = td
    
    md = tc.create_tree("md")
    md.set_parent_and_update_children(td)
    
    vis = tc.create_tree("vis", label="public")
    vis.set_parent_and_update_children(md)
    
    name = tc.create_tree("name", label="foo")
    name.set_parent_and_update_children(md)
    
    block = tc.create_tree("block")
    block.set_parent_and_update_children(md)
    
    s1 = tc.create_tree("s", label="s1")
    s1.set_parent_and_update_children(block)
    
    s2 = tc.create_tree("s", label="s2")
    s2.set_parent_and_update_children(block)
    
    s3 = tc.create_tree("s", label="s3")
    s3.set_parent_and_update_children(block)
    
    s4 = tc.create_tree("s", label="s4")
    s4.set_parent_and_update_children(block)
    return tc

def bottom_up_v1() -> TreeContext:
    tc = TreeContext()
    td = tc.create_tree("td")
    tc.root = td
    
    md = tc.create_tree("md")
    md.set_parent_and_update_children(td)
    
    vis = tc.create_tree("vis", label="private")
    vis.set_parent_and_update_children(md)
    
    name = tc.create_tree("name", label="bar")
    name.set_parent_and_update_children(md)
    
    block = tc.create_tree("block")
    block.set_parent_and_update_children(md)
    
    s1 = tc.create_tree("s", label="s1")
    s1.set_parent_and_update_children(block)
    
    s2 = tc.create_tree("s", label="s2")
    s2.set_parent_and_update_children(block)
    
    s3 = tc.create_tree("s", label="s3")
    s3.set_parent_and_update_children(block)
    
    s4 = tc.create_tree("s", label="s4")
    s4.set_parent_and_update_children(block)
    
    s5 = tc.create_tree("s", label="s5")
    s5.set_parent_and_update_children(block)
    return tc

    
def get_gumtree_pair() -> Tuple[TreeContext, TreeContext]:
    return (gum_tree_v0(), gum_tree_v1())

def get_bottom_up_pair() -> Tuple[Tree, Tree]:
    return (bottom_up_v0().root, bottom_up_v1().root)

def get_dummy_src() -> Tree:
    tc = TreeContext()
    a = tc.create_tree("0", label="a")
    tc.root = a
    
    b = tc.create_tree("1", label="b")
    b.set_parent_and_update_children(a)
    
    c = tc.create_tree("3", label="c")
    c.set_parent_and_update_children(b)
    
    d = tc.create_tree("3", label="d")
    d.set_parent_and_update_children(b)
    
    e = tc.create_tree("2", label="e")
    e.set_parent_and_update_children(a)
    
    return tc.root

def get_dummy_dst() -> Tree:
    tc = TreeContext()
    a = tc.create_tree("0", label="a")
    tc.root = a
    
    f = tc.create_tree("4", label="f")
    f.set_parent_and_update_children(a)
    
    b = tc.create_tree("1", label="b")
    b.set_parent_and_update_children(f)
    
    c = tc.create_tree("3", label="c")
    c.set_parent_and_update_children(b)
    
    d = tc.create_tree("3", label="d")
    d.set_parent_and_update_children(b)
    
    h = tc.create_tree("5", label="h")
    h.set_parent_and_update_children(b)
    
    i = tc.create_tree("2", label="i")
    i.set_parent_and_update_children(a)
    
    j = tc.create_tree("2", label="j")
    j.set_parent_and_update_children(i)
    
    return tc.root


def get_dummy_big() -> Tree:
    tc = TreeContext()
    a = tc.create_tree("0", label="a")
    tc.root = a
    
    b = tc.create_tree("1", label="b")
    b.set_parent_and_update_children(a)
    
    c = tc.create_tree("2", label="c")
    c.set_parent_and_update_children(b)
    
    d = tc.create_tree("2", label="d")
    d.set_parent_and_update_children(b)
    
    e = tc.create_tree("1", label="e")
    e.set_parent_and_update_children(a)
    
    f = tc.create_tree("1", label="f")
    f.set_parent_and_update_children(a)
    
    g = tc.create_tree("2", label="g")
    g.set_parent_and_update_children(f)
    
    h = tc.create_tree("3", label="h")
    h.set_parent_and_update_children(g)
    
    i = tc.create_tree("4", label="i")
    i.set_parent_and_update_children(h)
    
    j = tc.create_tree("4", label="j")
    j.set_parent_and_update_children(h)
    
    k = tc.create_tree("4", label="k")
    k.set_parent_and_update_children(h)
    
    l = tc.create_tree("2", label="l")
    l.set_parent_and_update_children(f)
    
    m = tc.create_tree("3", label="m")
    m.set_parent_and_update_children(l)
    
    return tc.root


def zs_v0() -> TreeContext:
    tc = TreeContext()
    a = tc.create_tree("0", label="a")
    tc.root = a
    
    b = tc.create_tree("0", label="b")
    b.set_parent_and_update_children(a)
    
    c = tc.create_tree("0", label="c")
    c.set_parent_and_update_children(a)
    
    d = tc.create_tree("0", label="d")
    d.set_parent_and_update_children(c)
    
    e = tc.create_tree("0", label="e")
    e.set_parent_and_update_children(c)
    
    f = tc.create_tree("0", label="f")
    f.set_parent_and_update_children(c)
    
    r1 = tc.create_tree("0", label="r1")
    r1.set_parent_and_update_children(c)
    
    return tc

def zs_v1() -> TreeContext:
    tc = TreeContext()
    
    z = tc.create_tree("0", label="z")
    tc.root = z
    
    a = tc.create_tree("0", label="a")
    a.set_parent_and_update_children(z)
    
    b = tc.create_tree("0", label="b")
    b.set_parent_and_update_children(a)
    
    c = tc.create_tree("0", label="c")
    c.set_parent_and_update_children(a)
    
    d = tc.create_tree("0", label="d")
    d.set_parent_and_update_children(c)
    
    y = tc.create_tree("1", label="y")
    y.set_parent_and_update_children(c)
    
    f = tc.create_tree("0", label="f")
    f.set_parent_and_update_children(c)
    
    r2 = tc.create_tree("0", label="r2")
    r2.set_parent_and_update_children(c)
    
    return tc

def get_zs_custom_pair() -> Tuple[TreeContext, TreeContext]:
    return (zs_v0(), zs_v1())


def zs_slide_v0() -> TreeContext:
    tc = TreeContext()
    
    _6 = tc.create_tree("0", label="6")
    tc.root = _6
    
    _5 = tc.create_tree("0", label="5")
    _5.set_parent_and_update_children(_6)
    
    _2 = tc.create_tree("0", label="2")
    _2.set_parent_and_update_children(_5)
    
    _1 = tc.create_tree("0", label="1")
    _1.set_parent_and_update_children(_2)
    
    _3 = tc.create_tree("0", label="3")
    _3.set_parent_and_update_children(_5)
    
    _4 = tc.create_tree("0", label="4")
    _4.set_parent_and_update_children(_5)
    return tc

def zs_slide_v1() -> TreeContext:
    tc = TreeContext()
    
    _6 = tc.create_tree("0", label="6")
    tc.root = _6
    
    _2 = tc.create_tree("0", label="2")
    _2.set_parent_and_update_children(_6)
    
    _1 = tc.create_tree("0", label="1")
    _1.set_parent_and_update_children(_2)
    
    _4 = tc.create_tree("0", label="4")
    _4.set_parent_and_update_children(_6)
    
    _3 = tc.create_tree("0", label="3")
    _3.set_parent_and_update_children(_4)
    
    _5 = tc.create_tree("0", label="5")
    _5.set_parent_and_update_children(_6)
    return tc

def get_zs_slide_pair() -> Tuple[TreeContext, TreeContext]:
    return (zs_slide_v0(), zs_slide_v1())


def get_subtree_src() -> Tree:
    tc = TreeContext()
    root = tc.create_tree("root")
    tc.root = root
    a = tc.create_tree("a")
    a.set_parent_and_update_children(root)
    
    b = tc.create_tree("b")
    b.set_parent_and_update_children(a)
    
    c = tc.create_tree("c", label="foo")
    c.set_parent_and_update_children(a)
    
    d = tc.create_tree("d")
    d.set_parent_and_update_children(root)
    

    a2 = tc.create_tree("a")
    a2.set_parent_and_update_children(root)
    
    b2 = tc.create_tree("b")
    b2.set_parent_and_update_children(a2)
    
    c2 = tc.create_tree("c", label="foo")
    c2.set_parent_and_update_children(a2)
    return tc.root


def action_v0() -> TreeContext:
    tc = TreeContext()
    
    a = tc.create_tree("0", label="a")
    tc.root = a
    
    e = tc.create_tree("0", label="e")
    e.set_parent_and_update_children(a)
    
    f = tc.create_tree("0", label="f")
    f.set_parent_and_update_children(e)
    
    b = tc.create_tree("0", label="b")
    b.set_parent_and_update_children(a)
    
    c = tc.create_tree("0", label="c")
    c.set_parent_and_update_children(b)
    
    d = tc.create_tree("0", label="d")
    d.set_parent_and_update_children(b)
    
    g = tc.create_tree("0", label="g")
    g.set_parent_and_update_children(a)
    
    h = tc.create_tree("0", label="h")
    h.set_parent_and_update_children(g)
    
    i = tc.create_tree("0", label="i")
    i.set_parent_and_update_children(a)
    
    j = tc.create_tree("0", label="j")
    j.set_parent_and_update_children(a)
    
    k = tc.create_tree("0", label="k")
    k.set_parent_and_update_children(j)
    return tc

def action_v1() -> TreeContext:
    tc = TreeContext()
    
    a = tc.create_tree("0", label="z")
    tc.root = a
    
    b = tc.create_tree("0", label="b")
    b.set_parent_and_update_children(a)
    
    c = tc.create_tree("0", label="c")
    c.set_parent_and_update_children(b)
    
    d = tc.create_tree("0", label="d")
    d.set_parent_and_update_children(b)
    
    h = tc.create_tree("0", label="h")
    h.set_parent_and_update_children(a)
    
    e = tc.create_tree("0", label="e")
    e.set_parent_and_update_children(h)
    
    y = tc.create_tree("0", label="y")
    y.set_parent_and_update_children(e)

    x = tc.create_tree("0", label="x")
    x.set_parent_and_update_children(a)
    
    w = tc.create_tree("0", label="w")
    w.set_parent_and_update_children(x)
    
    j = tc.create_tree("0", label="j")
    j.set_parent_and_update_children(a)
    
    u = tc.create_tree("0", label="u")
    u.set_parent_and_update_children(j)
    
    v = tc.create_tree("0", label="v")
    v.set_parent_and_update_children(u)
    
    k = tc.create_tree("0", label="k")
    k.set_parent_and_update_children(v)
    return tc

def get_action_pair() -> Tuple[TreeContext, TreeContext]:
    return (action_v0(), action_v1())