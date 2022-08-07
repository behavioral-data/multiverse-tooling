
from typing import Dict
from src.gumtree.main.gen.python_tree_generator import PythonTreeGenerator
from src.gumtree.main.gen.boba_python_tree_generator import BobaPythonTemplateTreeGeneator

from src.gumtree.main.gen.tree_generator import TreeGenerator

class TreeGeneratorFactory:
    def __init__(self, generator_name: str, extra_data: Dict):
        self.gen_name = generator_name
        self.extra_data = extra_data
        
    def get_generator(self) -> TreeGenerator:
        if self.gen_name == "python":
            return PythonTreeGenerator()
        elif self.gen_name == "boba_python_template":
            return BobaPythonTemplateTreeGeneator(self.extra_data)
        else:
            raise NotImplementedError(f"generator: {self.gen_name} is not implemented")