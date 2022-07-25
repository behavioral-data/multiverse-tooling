import src.gumtree.main.diff.io.tree_io_utils as tree_io_utils
from src.gumtree.main.trees.tree_context import TreeContext


def test_print_text_tree():
    tc = get_tree_context()
    print(str(tc))
    print(tc.root.to_tree_string())
    print(tc.root.children[0].to_tree_string())
    

def get_tree_context():
    tc = TreeContext()
    a = tc.create_tree("TYPE_0")
    tc.root = a
    
    b = tc.create_tree("TYPE_1")
    b.set_parent_and_update_children(a)
    
    c = tc.create_tree("TYPE_3", "a")
    c.set_parent_and_update_children(b)
    
    d = tc.create_tree("TYPE_3", "b")
    d.set_parent_and_update_children(b)
    
    e = tc.create_tree("TYPE_2")
    e.set_parent_and_update_children(a)
    
    return tc

if __name__ == '__main__':
    test_print_text_tree()