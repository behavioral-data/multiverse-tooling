from abc import ABC, abstractmethod

from typing import Dict
from src.gumtree.main.diff.diff import Diff


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
                               self.generator, self.matcher, self.configurations)
        
    def save_diff_to_file(self, save_path):
        with open(save_path, 'w') as f:
            f.write(self.run())

    
    