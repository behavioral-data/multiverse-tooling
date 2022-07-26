

from typing import Dict

from src.gumtree.main.diff.actions.action import Action
from src.gumtree.main.diff.actions.delete import Delete
from src.gumtree.main.diff.actions.insert import Insert
from src.gumtree.main.diff.actions.tree_addition import TreeInsert
from src.gumtree.main.diff.actions.tree_delete import TreeDelete
from src.gumtree.main.diff.chawathe_script_generator import ChawatheScriptGenerator
from src.gumtree.main.diff.edit_script import EditScript, EditScriptGenerator
from src.gumtree.main.matchers.mapping_store import MappingStore
from src.gumtree.main.trees.tree import Tree


class SimplifiedChawatheScriptGenerator(EditScriptGenerator):
    
    @staticmethod
    def compute_actions(mappings: MappingStore) -> EditScript:
        actions = ChawatheScriptGenerator.compute_actions(mappings)
        return SimplifiedChawatheScriptGenerator.simplify(actions)
    
    @staticmethod
    def simplify(actions: EditScript) -> EditScript:
        added_trees: Dict[Tree, Action] = {}
        deleted_trees: Dict[Tree, Action] = {}
        
        for a in actions:
            if isinstance(a, Insert):
                added_trees[a.node] = a
            elif isinstance(a, Delete):
                deleted_trees[a.node] = a
    
        for t in added_trees:
            if (t.parent in added_trees and 
                set(t.parent.get_descendents()).issubset(set(added_trees.keys()))):
                actions.remove(added_trees[t])
            else:
                if len(t.children) > 0 and set(t.get_descendents()).issubset(set(added_trees.keys())):
                    original_action: Insert = added_trees[t]
                    ti = TreeInsert(original_action.node, original_action.parent, original_action.pos)
                    index = actions.last_index_of(original_action)
                    actions.add(ti, index=index)
                    actions.remove_ind(index + 1)
        
        for t in deleted_trees:
            if (t.parent in deleted_trees and 
                set(t.parent.get_descendents()).issubset(set(deleted_trees.keys()))):
                actions.remove(deleted_trees[t])
            else:
                if len(t.children) > 0 and set(t.get_descendents()).issubset(set(deleted_trees.keys())):
                    original_action: Delete = deleted_trees[t]
                    ti = TreeDelete(original_action.node)
                    index = actions.last_index_of(original_action)
                    actions.add(ti, index=index)
                    actions.remove_ind(index + 1)
        return actions