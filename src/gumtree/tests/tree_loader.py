from re import X
from typing import Tuple
from src.gumtree.main.trees.tree_context import TreeContext
from src.gumtree.main.trees.tree import Tree

from src.gumtree.main.trees.node_constants import BOBA_VAR

from src.gumtree.main.trees.boba_tree import BobaTree


def gum_tree_v0() -> TreeContext:
    """
    DefaultTree: 0 (a) 
        DefaultTree: 0 (e) 
            DefaultTree: 0 (f) 
        DefaultTree: 0 (b) 
            DefaultTree: 0 (c) 
            DefaultTree: 0 (d) 
        DefaultTree: 0 (g) 
    """
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
    """
    DefaultTree: 0 (z) 
        DefaultTree: 0 (b) 
            DefaultTree: 0 (c) 
            DefaultTree: 0 (d) 
        DefaultTree: 1 (h) 
            DefaultTree: 0 (e) 
                DefaultTree: 0 (y) 
        DefaultTree: 0 (g) 
    """
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
    """
    DefaultTree: td
        DefaultTree: md
            DefaultTree: vis (public) 
            DefaultTree: name (foo) 
            DefaultTree: block
                DefaultTree: s (s1) 
                DefaultTree: s (s2) 
                DefaultTree: s (s3) 
                DefaultTree: s (s4) 
    """
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
    """
    DefaultTree: td
        DefaultTree: md
            DefaultTree: vis (private) 
            DefaultTree: name (bar) 
            DefaultTree: block
                DefaultTree: s (s1) 
                DefaultTree: s (s2) 
                DefaultTree: s (s3) 
                DefaultTree: s (s4) 
                DefaultTree: s (s5) 
    """
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
    """ 
    DefaultTree: 0 (a) 
        DefaultTree: 1 (b) 
            DefaultTree: 3 (c) 
            DefaultTree: 3 (d) 
        DefaultTree: 2 (e) 
    """
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
    """
    DefaultTree: 0 (a) 
        DefaultTree: 4 (f) 
            DefaultTree: 1 (b) 
                DefaultTree: 3 (c) 
                DefaultTree: 3 (d) 
                DefaultTree: 5 (h) 
        DefaultTree: 2 (i) 
            DefaultTree: 2 (j) 
    """
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
    """ 
    DefaultTree: 0 (a) 
        DefaultTree: 1 (b) 
            DefaultTree: 2 (c) 
            DefaultTree: 2 (d) 
        DefaultTree: 1 (e) 
        DefaultTree: 1 (f) 
            DefaultTree: 2 (g) 
                DefaultTree: 3 (h) 
                    DefaultTree: 4 (i) 
                    DefaultTree: 4 (j) 
                    DefaultTree: 4 (k) 
            DefaultTree: 2 (l) 
                DefaultTree: 3 (m) 
    """
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
    """ 
    DefaultTree: 0 (a) 
        DefaultTree: 0 (b) 
        DefaultTree: 0 (c) 
            DefaultTree: 0 (d) 
            DefaultTree: 0 (e) 
            DefaultTree: 0 (f) 
            DefaultTree: 0 (r1) 
    """
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
    """ 
    DefaultTree: 0 (z) 
        DefaultTree: 0 (a) 
            DefaultTree: 0 (b) 
            DefaultTree: 0 (c) 
                DefaultTree: 0 (d) 
                DefaultTree: 1 (y) 
                DefaultTree: 0 (f) 
                DefaultTree: 0 (r2) 
    """
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
    """ 
    DefaultTree: 0 (6) 
        DefaultTree: 0 (5) 
            DefaultTree: 0 (2) 
                DefaultTree: 0 (1) 
            DefaultTree: 0 (3) 
            DefaultTree: 0 (4)
    """
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
    """ 
    DefaultTree: 0 (6) 
        DefaultTree: 0 (2) 
            DefaultTree: 0 (1) 
        DefaultTree: 0 (4) 
            DefaultTree: 0 (3) 
        DefaultTree: 0 (5)
    """
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
    """ 
    DefaultTree: root
        DefaultTree: a
            DefaultTree: b
            DefaultTree: c (foo) 
        DefaultTree: d
        DefaultTree: a
            DefaultTree: b
            DefaultTree: c (foo)
    """
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
    """
    DefaultTree: 0 (a) 
        DefaultTree: 0 (e) 
            DefaultTree: 0 (f) 
        DefaultTree: 0 (b) 
            DefaultTree: 0 (c) 
            DefaultTree: 0 (d) 
        DefaultTree: 0 (g) 
            DefaultTree: 0 (h) 
        DefaultTree: 0 (i) 
        DefaultTree: 0 (j) 
            DefaultTree: 0 (k) 
    """
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
    """
    DefaultTree: 0 (z) 
        DefaultTree: 0 (b) 
            DefaultTree: 0 (c) 
            DefaultTree: 0 (d) 
        DefaultTree: 0 (h) 
            DefaultTree: 0 (e) 
                DefaultTree: 0 (y) 
        DefaultTree: 0 (x) 
            DefaultTree: 0 (w) 
        DefaultTree: 0 (j) 
            DefaultTree: 0 (u) 
                DefaultTree: 0 (v) 
				DefaultTree: 0 (k)
    """
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

def get_boba_big() -> BobaTree:
    """ 
    BobaTree: 0 (a) 
        BobaTree: 1 (b) 
            BobaTree: 2 (c) 
            BobaTree: BobaVar (d) # 5 nodes
        BobaTree: 1 (e) 
        BobaTree: 1 (f) 
            BobaTree: 2 (g) 
                BobaTree: 3 (h) 
                    BobaTree: 4 (i) 
                    BobaTree: BobaVar (j)   # 9 nodes
                    BobaTree: BobaVar (k)   # 3 nodes
            BobaTree: 2 (l) 
                BobaTree: 3 (m) 
    """
    tc = TreeContext()
    a = tc.create_boba_tree("0", label="a")
    tc.root = a
    
    b = tc.create_boba_tree("1", label="b")
    b.set_parent_and_update_children(a)
    
    c = tc.create_boba_tree("2", label="c")
    c.set_parent_and_update_children(b)
    
    d = tc.create_boba_tree(BOBA_VAR, label="d")
    d.num_boba_var_nodes = 5
    d.set_parent_and_update_children(b)
    
    e = tc.create_boba_tree("1", label="e")
    e.set_parent_and_update_children(a)
    
    f = tc.create_boba_tree("1", label="f")
    f.set_parent_and_update_children(a)
    
    g = tc.create_boba_tree("2", label="g")
    g.set_parent_and_update_children(f)
    
    h = tc.create_boba_tree("3", label="h")
    h.set_parent_and_update_children(g)
    
    i = tc.create_boba_tree("4", label="i")
    i.set_parent_and_update_children(h)
    
    j = tc.create_boba_tree(BOBA_VAR, label="j")
    j.num_boba_var_nodes = 9

    j.set_parent_and_update_children(h)
    
    k = tc.create_boba_tree(BOBA_VAR, label="k")
    k.num_boba_var_nodes = 3
    k.set_parent_and_update_children(h)
    
    l = tc.create_boba_tree("2", label="l")
    l.set_parent_and_update_children(f)
    
    m = tc.create_boba_tree("3", label="m")
    m.set_parent_and_update_children(l)
    
    return tc.root

def get_action_pair() -> Tuple[TreeContext, TreeContext]:
    return (action_v0(), action_v1())

