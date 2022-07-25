from __future__ import annotations
from operator import attrgetter
from typing import Dict, TYPE_CHECKING
from abc import ABC, abstractmethod
from io import IOBase, StringIO
from src.gumtree.main.trees.tree_visitor import TreeVisitor, DefaultTreeVisitor

if TYPE_CHECKING:
    from src.gumtree.main.trees.tree import Tree
    from src.gumtree.main.trees.tree_context import TreeContext

class TreeFormatter(ABC):
    @abstractmethod
    def start_serialization(self):
        pass
    
    @abstractmethod
    def end_prolog(self):
        pass
    
    @abstractmethod
    def stop_serialization(self):
        pass
    
    @abstractmethod
    def start_tree(self, tree: Tree):
        pass
    
    @abstractmethod
    def end_tree_prolog(self, tree: Tree):
        pass
    
    @abstractmethod
    def end_tree(self, tree: Tree):
        pass
    
    @abstractmethod
    def close(self):
        pass
    
    @abstractmethod
    def serialize_attribute(self, name: str, value: str):
        pass
    
    
class AbstractSerializer(ABC):
    @abstractmethod
    def write_to(self, writer: IOBase):
        pass
    
    def write_to_file(self, file):
        if type(file) is str:
            f = open(file, "w")
            self.write_to(f)
            f.close()
        else:
            self.write_to(file)
            
    def __str__(self):
        f = StringIO()
        self.write_to(f)
        return f.getvalue()
     
    
class TreeSerializer(AbstractSerializer, ABC):
    def __init__(self, ctx: TreeContext, root: Tree):
        self.context = ctx
        self.root = root
        
        
    @abstractmethod
    def new_formatter(self, ctx: TreeContext, writer: IOBase) -> TreeFormatter:
        pass

    def write_to(self, writer: IOBase):
        formatter = self.new_formatter(self.context, writer)
        try:
            self.write_tree(formatter, self.root)
        finally:
            formatter.close()
            
    def write_tree(self, formatter: TreeFormatter, root: Tree):
        formatter.start_serialization()
        formatter.end_prolog()
        
        def start_tree(tree: Tree):
            assert tree is not None
            formatter.start_tree(tree)
            self.write_attributes(formatter, tree.metadata)
            formatter.end_tree_prolog(tree)
        
        def end_tree(tree: Tree):
            formatter.end_tree(tree)
        
        TreeVisitor.visit_tree(root, DefaultTreeVisitor(), 
                               start_tree_func=start_tree,
                               end_tree_func=end_tree)
        formatter.stop_serialization()
        
    def write_attributes(self, formatter: TreeFormatter, attributes: Dict[str, ]):
        for k, v in attributes.items():
            formatter.serialize_attribute(k, v)

  
class TreeFormatterAdapter(TreeFormatter):
    def __init__(self, ctx: TreeContext):
        self.context = ctx
        
    def start_serialization(self):
        pass
    
    def end_prolog(self):
        pass
    
    def stop_serialization(self):
        pass
    
    def start_tree(self, tree: Tree):
        pass
    
    def end_tree_prolog(self, tree: Tree):
        pass
    
    def end_tree(self, tree: Tree):
        pass
    
    def close(self):
        pass
    
    def serialize_attribute(self, name: str, value: str):
        pass
    

class AbstractTextFormatter(TreeFormatterAdapter, ABC):
    def __init__(self, writer, ctx: TreeContext):
        super().__init__(ctx)
        self.writer = writer
        self.level = 0
    
    def indent(self, level: int , prefix: str):
        for i in range(level):
            self.writer.write(prefix)
    
    def start_tree(self, tree: Tree):
        if self.level != 0:
            self.writer.write("\n")
        self.indent(self.level, prefix="\t")
        self.level += 1
        self.write_tree(tree)
        
    @abstractmethod
    def write_tree(self, tree: Tree):
        pass
    
    def end_tree(self, tree: Tree):
        self.level -= 1 
        
class TextFormatter(AbstractTextFormatter):
    def write_tree(self, tree: Tree):
        self.writer.write(str(tree))

class ShortTextFormatter(AbstractTextFormatter):
    def write_tree(self, tree: Tree):
        self.writer.write(str(tree))

def to_short_text(root: Tree) -> TreeSerializer:
    class ShortTextSerializer(TreeSerializer):
        def new_formatter(self, ctx: TreeContext, writer: IOBase) -> TreeFormatter:
            return ShortTextFormatter(writer, ctx)
        
    return ShortTextSerializer(None, root)

def to_text(ctx: TreeContext, root=None):
    if root is None:
        root = ctx.root
    class TextSerializer(TreeSerializer):
        def new_formatter(self, ctx: TreeContext, writer: IOBase) -> TreeFormatter:
            return TextFormatter(writer, ctx)
    return TextSerializer(ctx, root)
    
