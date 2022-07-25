
from src.gumtree.main.trees.tree_context import TreeContext
from src.gumtree.main.matchers.default_priority_tree_queue import DefaultPriorityTreeQueue
from src.gumtree.tests.tree_loader import get_dummy_src

def test_pop_open_with_height():
    tree = get_dummy_src()
    queue = DefaultPriorityTreeQueue(tree, 0, DefaultPriorityTreeQueue.HEIGHT_PRIORITY_CALCULATOR)
    assert(2 == queue.current_priority())
    p = queue.pop_open()
    assert(1 == len(p))
    assert(1 == queue.current_priority())
    p = queue.pop_open()
    assert(0 == queue.current_priority())
    assert(1 == len(p))
    p = queue.pop_open()
    assert(queue.is_empty())
    assert(3 == len(p))
    
    
def test_pop_open_with_size():
    tree = get_dummy_src()
    queue = DefaultPriorityTreeQueue(tree, 0,
            DefaultPriorityTreeQueue.SIZE_PRIORITY_CALCULATOR)
    assert(5 == queue.current_priority())
    p = queue.pop_open()
    assert(1 == len(p))
    assert(3 == queue.current_priority())
    p = queue.pop_open()
    assert(1 == len(p))
    assert(1 == queue.current_priority())
    p = queue.pop_open()
    assert(3 == len(p))
    assert(queue.is_empty())
    
def test_pop_open_with_size_and_min_priority():
    tree = get_dummy_src()
    queue = DefaultPriorityTreeQueue(tree, 2, DefaultPriorityTreeQueue.SIZE_PRIORITY_CALCULATOR)
    assert(5 == queue.current_priority())
    p = queue.pop_open()
    assert(1 == len(p))
    assert(3 == queue.current_priority())
    p = queue.pop_open()
    assert(1 == len(p))
    assert(queue.is_empty())

def test_syncrhonize():
    tree = get_dummy_src()
    queue1 = DefaultPriorityTreeQueue(tree, 0, DefaultPriorityTreeQueue.HEIGHT_PRIORITY_CALCULATOR)
    queue2 = DefaultPriorityTreeQueue(tree, 0, DefaultPriorityTreeQueue.HEIGHT_PRIORITY_CALCULATOR)
    queue2.pop_open()
    assert(2 == queue1.current_priority())
    assert(1 == queue2.current_priority())
    DefaultPriorityTreeQueue.synchronize(queue1, queue2)
    assert(1 == queue1.current_priority())
    assert(1 == queue2.current_priority())

    queue3 = DefaultPriorityTreeQueue(tree, 0, DefaultPriorityTreeQueue.HEIGHT_PRIORITY_CALCULATOR)
    queue3.clear()
    DefaultPriorityTreeQueue.synchronize(queue2, queue3)
    assert(queue2.is_empty())
    assert(queue3.is_empty())
    
    
def test_synchronize():
    tree = get_dummy_src()
    

if __name__ == "__main__":
    test_pop_open_with_height()
    test_pop_open_with_size()
    test_pop_open_with_size_and_min_priority()
    test_syncrhonize()
    print('done')