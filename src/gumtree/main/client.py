from abc import ABC, abstractmethod

from typing import Dict
from src.gumtree.main.diff.diff import Diff
from src.gumtree.main.diff.io.action_io_utils import to_text, to_json
from io import StringIO
from src.gumtree.main.trees.tree import Tree

from src.gumtree.main.trees.tree_context import TreeContext

class Client(ABC):
    DEFAULT_MATCHER = "classic"
    DEFAULT_GENERATOR = "python"
    
    def __init__(self, src_code, dst_code, configurations: Dict=None):
        self.src_code = src_code
        self.dst_code = dst_code
        self.configurations = {} if configurations is None else configurations
        self.configure()
        
    
    def configure(self, configurations: Dict=None):
        configurations = self.configurations if configurations is None else configurations
        self.generator = configurations.get("generator", self.DEFAULT_GENERATOR)
        self.matcher = configurations.get("matcher", self.DEFAULT_MATCHER)
    
    @abstractmethod
    def run(self) -> str:
        pass
    
    def get_diff(self) -> Diff:
        return Diff.compute_from_strs(self.src_code, self.dst_code, 
                               self.generator, self.matcher)
        
    def save_diff_to_file(self, save_path):
        with open(save_path, 'w') as f:
            f.write(self.run())
        

class TextDiff(Client):
    
    def __init__(self, src_code, dst_code, formatter="text"):
        super().__init__(src_code, dst_code)
        self.formatter = formatter
        
    def run(self):
        diff: Diff = self.get_diff()
        if self.formatter == "text":
            diff_str = str(to_text(diff.src, diff.edit_script, diff.mappings))
        elif self.formatter == "json":
            diff_str = str(to_json(diff.src, diff.edit_script, diff.mappings))
        return diff_str
        
    
class DotDiff(Client):
    def __init__(self, src_code, dst_code):
        super().__init__(src_code, dst_code)
        self.src_code = src_code
        self.dst_code = dst_code
        self.diff = self.get_diff()
        self.classifier = self.diff.createAllNodeClassifier()
        
    def run(self) -> str:
        writer = StringIO()
        writer.write("digraph G {\n")
        writer.write("\tnode [style=filled]\n")
        writer.write("\tsubgraph cluster_src {\n")
        self.write_tree(self.diff.src, writer)
        writer.write("\t}\n")
        writer.write("\tsubgraph cluster_dst {\n")
        self.write_tree(self.diff.dst, writer)
        writer.write("\t}\n")
        for m in self.diff.mappings:
            writer.write("\t{} -> {} [style=dashed]\n".format(
                    self.get_dot_id(self.diff.src, m[0]), self.get_dot_id(self.diff.dst, m[1])))
        writer.write("}\n")
        print(writer)
        return writer.getvalue()
    
    def write_tree(self, context: TreeContext, writer: StringIO):
        for tree in context.root.pre_order():
            fillColor = self.get_dot_color(tree)
            writer.write("\t\t{} [label=\"{}\", color={}]\n".format(
                    self.get_dot_id(context, tree), self.get_dot_label(tree), fillColor))
            if (tree.parent is not None):
                writer.write("\t\t{} -> {}\n".format(
                        self.get_dot_id(context, tree.parent), self.get_dot_id(context, tree)))
    


    def get_dot_color(self, tree: Tree):
        if tree in self.classifier.get_deleted_srcs():
            return "red"
        elif tree in self.classifier.get_inserted_dsts():
            return "green"
        elif tree in self.classifier.get_moved_dsts() or tree in self.classifier.get_moved_srcs():
            return "blue"
        elif tree in self.classifier.get_updated_dsts() or tree in self.classifier.get_updated_srcs():
            return "orange"
        else:
            return "lightgrey"


    def get_dot_id(self, context: TreeContext, tree: Tree):
        context_str = "src" if context == self.diff.src else "dst"
        return "n_" + context_str + "_" + str(tree.tree_metrics.position)


    def get_dot_label(self, tree: Tree):
        label = str(tree)
        if  "\"" in label or  "\\s" in label:
            label = label.replace("\"", "").replace("\\s", "").replace("\\\\", "")
        if len(label) > 30:
            label = label[:30]
        return label

        
if __name__ == "__main__":
    from src.utils import VIZ_DIR
    import os.path as osp
    FUNC1 = """
class Test:
    def foo(self, i):
        if i == 0:
            return "Foo!"
    """

    FUNC2 = """
class Test:
    def foo(self, i, j):
        if i == j:
            return "Bar"
        elif i == -1:
            return "Foo!"
    """
    
    client = TextDiff(FUNC1, FUNC2, formatter="json")
    s1 = client.run()
    
    dot_client = DotDiff(FUNC1, FUNC2)
    s2 = dot_client.run()
    
    save_path = osp.join(VIZ_DIR, "test_diff.dot")
    dot_client.save_diff_to_file(save_path)
    print('here')
    
    