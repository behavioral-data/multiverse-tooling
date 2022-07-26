from abc import ABC, abstractmethod
from src.gumtree.main.diff.io.tree_io_utils import AbstractSerializer
from src.gumtree.main.diff.edit_script import EditScript

from src.gumtree.main.matchers.mapping_store import MappingStore
from src.gumtree.main.trees.tree_context import TreeContext

from src.gumtree.main.diff.actions.insert import Insert
from src.gumtree.main.diff.actions.move import Move
from src.gumtree.main.diff.actions.tree_addition import TreeInsert
from src.gumtree.main.diff.actions.tree_delete import TreeDelete
from src.gumtree.main.diff.actions.update import Update
from io import IOBase, StringIO

from src.gumtree.main.trees.tree import Tree

from src.gumtree.main.diff.actions.delete import Delete

from src.gumtree.main.diff.actions.action import Action

import json

class ActionFormatter(ABC):
    @abstractmethod
    def start_output(selfself):
        pass

    @abstractmethod
    def end_output(selfself):
        pass

    @abstractmethod
    def start_matches(selfself):
        pass

    @abstractmethod
    def match(self, srcNode: Tree, destNode: Tree):
        pass

    @abstractmethod
    def end_matches(selfself):
        pass

    @abstractmethod
    def start_actions(selfself):
        pass

    @abstractmethod
    def insert_root(self, action: Insert, node: Tree):
        pass

    @abstractmethod
    def insert_action(self, action: Insert, node: Tree, parent: Tree, index: int):
        pass

    @abstractmethod
    def insert_tree_action(self, action: TreeInsert, node: Tree, parent: Tree, index: int):
        pass

    @abstractmethod
    def move_action(self, action: Move, src: Tree, dst: Tree, index: int):
        pass

    @abstractmethod
    def update_action(self, action: Update, src: Tree, dst: Tree):
        pass

    @abstractmethod
    def delete_action(self, action: Delete, node: Tree):
        pass

    @abstractmethod
    def delete_tree_action(self, action: TreeDelete, node: Tree):
        pass

    @abstractmethod
    def end_actions(self):
        pass
    
        
class ActionSerializer(AbstractSerializer):
    def __init__(self, context: TreeContext, mappings: MappingStore, 
                 actions: EditScript):
        self.context = context
        self.mappings = mappings
        self.actions = actions
        
    @abstractmethod
    def new_formatter(self, ctx: TreeContext, writer: IOBase) -> ActionFormatter:
        pass
    
    def write_to(self, writer: IOBase):
        fmt: ActionFormatter = self.new_formatter(self.context, writer)
        fmt.start_output()
        fmt.start_matches()
        for m in self.mappings:
            fmt.match(m[0], m[1])
        fmt.end_matches()
        
        fmt.start_actions()
        for a in self.actions:
            src = a.node
            if isinstance(a, Move):
                dst = self.mappings.get_dst_for_src(src)
                fmt.move_action(a, src, dst.parent, a.pos)
            elif isinstance(a, Update):
                dst = self.mappings.get_dst_for_src(src)
                fmt.update_action(a, src, dst)
            elif isinstance(a, Insert):
                dst = a.node
                if (dst.is_root()):
                    fmt.insert_root(a, src)
                else:
                    fmt.insert_action(a, src, dst.parent, dst.parent.get_child_position(dst))
            elif isinstance(a, Delete):
                fmt.delete_action(a, src)
            elif isinstance(a, TreeInsert):
                dst = a.node
                fmt.insert_tree_action( a, src, dst.parent, dst.parent.get_child_position(dst))
            elif isinstance(a,  TreeDelete):
                fmt.delete_tree_action(a, src)
                
        fmt.end_actions()
        fmt.end_output()
    
    
class TextFormatter(ActionFormatter):

    def __init__(self, ctx: TreeContext, writer: IOBase):
        self.context = ctx
        self.writer = writer

    def start_output(self):
        pass 
    
    def end_output(self):
        pass
    
    def start_matches(self):
        pass
    
    def match(self, src_node: Tree, dst_node: Tree):
        self.write(f"===\nmatch\n---\n{self.to_string(src_node)}\n{self.to_string(dst_node)}")

    def end_matches(self):
        pass
    
    def start_actions(self):
        pass
    
    def insert_root(self, action: Insert, node: Tree):
        self.write(str(action))

    def insert_action(self, action: Insert, node: Tree, parent: Tree, index: int):
        self.write(str(action))

    def insert_tree_action(self, action: TreeInsert, node: Tree, parent: Tree, index: int):
        self.write(str(action))

    def move_action(self, action: Move, src: Tree, dst: Tree, position:int):
        self.write(str(action))

    def update_action(self, action: Update, src: Tree, dst: Tree):
        self.write(str(action))

    def delete_action(self, action: Delete, node: Tree):
        self.write(str(action))

    def delete_tree_action(self, action: TreeDelete, node: Tree):
        self.write(str(action))

    def end_actions(self):
        pass

    def write(self, fmt: str):
        self.writer.write(fmt)
        self.writer.write("\n")

    def to_string(self,node: Tree):
        return str(node)

class JsonFormatter(ActionFormatter):
    
    def __init__(self, ctx: TreeContext, writer: IOBase):
        self.context = ctx
        self.writer = writer
        self.output_dict = {}
        self.matches_dict = {}

    def start_output(self):
        pass 
    
    def end_output(self):
        self.writer.write(json.dumps(self.output_dict, indent=2))
    
    def start_matches(self):
        self.output_dict["matches"] = []
    
    def match(self, src_node: Tree, dst_node: Tree):
        self.output_dict["matches"].append({"src": str(src_node),
                                            "dest": str(dst_node)})

    def end_matches(self):
        pass
    
    def start_actions(self):
        self.output_dict["actions"] = []
    
    def start(self, action: Action, src:Tree):
        return {"action": action.get_name(), "tree": str(src)}
        
    def insert_root(self, action: Insert, node: Tree):
        self.output_dict["actions"].append(self.start(action, node))

    def insert_action(self, action: Insert, node: Tree, parent: Tree, index: int):
        dic = self.start(action, node)
        dic["parent"] = str(parent)
        dic["at"] = index
        self.output_dict["actions"].append(dic)

    def insert_tree_action(self, action: TreeInsert, node: Tree, parent: Tree, index: int):
        dic = self.start(action, node)
        dic["parent"] = str(parent)
        dic["at"] = index
        self.output_dict["actions"].append(dic)

    def move_action(self, action: Move, src: Tree, dst: Tree, index:int):
        dic = self.start(action, src)
        dic["parent"] = str(dst)
        dic["at"] = index
        self.output_dict["actions"].append(dic)

    def update_action(self, action: Update, src: Tree, dst: Tree):
        dic = self.start(action, src)
        dic["label"] = dst.label
        self.output_dict["actions"].append(dic)
        
    def delete_action(self, action: Delete, node: Tree):
        self.output_dict["actions"].append(self.start(action, node))

    def delete_tree_action(self, action: TreeDelete, node: Tree):
        self.output_dict["actions"].append(self.start(action, node))

    def end_actions(self):
        pass
    
class TextActionSerializer(ActionSerializer):
    def new_formatter(self, ctx: TreeContext, writer: IOBase):
        return TextFormatter(ctx, writer)

def to_text(ctx: TreeContext, actions: EditScript, mappings: MappingStore) -> ActionSerializer:
    return TextActionSerializer(ctx, mappings, actions)


class JsonActionSerializer(ActionSerializer):
    def new_formatter(self, ctx: TreeContext, writer: IOBase) -> ActionFormatter:
        return JsonFormatter(ctx, writer)
    
def to_json(ctx: TreeContext, actions: EditScript, mappings: MappingStore) -> ActionSerializer:
    return JsonActionSerializer(ctx, mappings, actions)