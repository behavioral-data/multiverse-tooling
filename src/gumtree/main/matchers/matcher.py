
from abc import ABC, abstractmethod

from src.gumtree.main.matchers.mapping_store import MappingStore
from typing import Dict
from src.gumtree.main.trees.tree import Tree

class Matcher(ABC):
    
    @abstractmethod
    def configure(self, configurations: Dict):
        pass
    
    @abstractmethod
    def match(self, src: Tree, dst: Tree, mappings: MappingStore):
        pass
    