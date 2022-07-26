from abc import ABC, abstractmethod
from src.gumtree.main.diff.actions.action import Action
from src.gumtree.main.matchers.mapping_store import MappingStore


class EditScript:
    def __init__(self):
        self.actions = []
        
    def __iter__(self):
        return iter(self.actions)
    
    def add(self, action: Action, index: int=None):
        if index is None:
            self.actions.append(action)
        else:
            self.actions.insert(index, action)
        
    def get(self, index: int):
        return self.actions[index]
    
    def remove(self, action: Action):
        try:
            self.actions.remove(action)
        except ValueError as e:
            return False
        return True
    
    def __contains__(self, action: Action):
        return action in self.actions
    
    def __len__(self):
        return len(self.actions)
    
    def remove_ind(self, index: int):
        return self.actions.pop(index)
    
    def as_list(self):
        return self.actions
    
    def last_index_of(self, action: Action):
        return len(self.actions) - 1 - self.actions[::-1].index(action)
    
    
class EditScriptGenerator(ABC):
    
    @abstractmethod
    def compute_actions(mappings: MappingStore) -> EditScript:
        pass