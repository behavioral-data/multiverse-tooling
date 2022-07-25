from src.gumtree.main.matchers.composite_matchers import ClassicGumTree
from src.gumtree.main.matchers.mapping_store import MappingStore
from src.gumtree.main.trees.default_tree import DefaultTree
from src.gumtree.main.diff.chawathe_script_generator import ChawatheScriptGenerator

from src.gumtree.main.trees.tree import Tree
# TODO 07/222 Implement Edit Script Algorithm so that we could write test program

def test_stability():
    previous_script = None
    src = get_src_tree()
    dst = get_dst_tree()
    for i in range(20):
        matcher = ClassicGumTree()
        mapping_store = matcher.match(src, dst, MappingStore(src, dst))
        script_generator = ChawatheScriptGenerator
        current_script = script_generator.compute_actions(mapping_store)
        if previous_script is None:
            previous_script = current_script
        else:
            assert all([a == b for a, b in zip(previous_script, current_script)])
            previous_script = current_script

    
def generate_tree(node_type, label=None) -> Tree:
    itree = DefaultTree(node_type, label)
    return itree

def get_src_tree():
    tree0 = generate_tree("Empty")
    tree1 = generate_tree("Identifier", "delete")
    tree2 = generate_tree("Identifier", "value")
    tree3 = generate_tree("Call")
    tree3.add_child(tree0)
    tree3.add_child(tree1)
    tree3.add_child(tree2)

    tree4 = generate_tree("Integer", "1")
    tree5 = generate_tree("GreaterThan")
    tree5.add_child(tree3)
    tree5.add_child(tree4)

    tree6 = generate_tree("Empty")
    tree7 = generate_tree("Identifier", "move")
    tree8 = generate_tree("Identifier", "value")
    tree9 = generate_tree("TextElement")
    tree10 = generate_tree("Call")
    tree10.add_child(tree6)
    tree10.add_child(tree7)
    tree10.add_child(tree8)
    tree10.add_child(tree9)

    tree11 = generate_tree("Boolean")
    tree12 = generate_tree("Return")
    tree12.add_child(tree11)

    tree13 = generate_tree("Boolean")
    tree14 = generate_tree("Return")
    tree14.add_child(tree13)

    tree15 = generate_tree("If")
    tree15.add_child(tree5)
    tree15.add_child(tree10)
    tree15.add_child(tree12)
    tree15.add_child(tree14)

    tree17 = generate_tree("Identifier", "value")
    tree18 = generate_tree("Identifier", "str")
    tree19 = generate_tree("Annotation")
    tree19.add_child(tree17)
    tree19.add_child(tree18)

    tree20 = generate_tree("Function")
    tree20.add_child(tree15)
    tree16 = generate_tree("Identifier", "update")
    tree20.add_child(tree16)
    tree20.add_child(tree19)

    return tree20

def get_dst_tree():
    tree21 = generate_tree("Empty")
    tree22 = generate_tree("Identified", "add")
    tree23 = generate_tree("Identifier", "value")
    tree24 = generate_tree("Call")
    tree24.add_child(tree21)
    tree24.add_child(tree22)
    tree24.add_child(tree23)
    
    tree25 = generate_tree("Integer", "10")
    tree26 = generate_tree("GreaterThan")
    
    tree26.add_child(tree24)
    tree26.add_child(tree25)
    
    tree27 = generate_tree("Empty")
    tree28 = generate_tree("Identifier", "move")
    tree29 = generate_tree("Identifier", "value")
    tree30 = generate_tree("TextElement")
    tree31 = generate_tree("Call")
    tree31.add_child(tree27)
    tree31.add_child(tree28)
    tree31.add_child(tree29)
    tree31.add_child(tree30)

    tree32 = generate_tree("Boolean")
    tree33 = generate_tree("Return")
    tree33.add_child(tree32)

    tree34 = generate_tree("Empty")
    tree35 = generate_tree("Identifier", "map")
    tree36 = generate_tree("Identifier", "value")
    tree37 = generate_tree("Call")
    tree37.add_child(tree34)
    tree37.add_child(tree35)
    tree37.add_child(tree36)

    tree38 = generate_tree("Return")
    tree38.add_child(tree37)

    tree39 = generate_tree("If")
    tree39.add_child(tree26)
    tree39.add_child(tree31)
    tree39.add_child(tree33)
    tree39.add_child(tree38)



    tree41 = generate_tree("Identifier", "value")
    tree42 = generate_tree("Identifier", "str")
    tree43 = generate_tree("Annotation")
    tree43.add_child(tree41)
    tree43.add_child(tree42)

    tree44 = generate_tree("Function")
    tree44.add_child(tree39)
    tree40 = generate_tree("Identifier", "update")
    tree44.add_child(tree40)
    tree44.add_child(tree43)
    
    return tree44


if __name__ == "__main__":
    test_stability()