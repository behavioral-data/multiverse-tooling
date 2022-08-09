
from typing import Dict
from src.gumtree.main.gen.python_tree_generator import PythonTreeGenerator
from src.gumtree.main.gen.boba_tree_generator import BobaPythonTemplateTreeGeneator, BobaRTemplateGenerator

from src.gumtree.main.gen.tree_generator import TreeGenerator

from src.gumtree.main.gen.r_tree_generator import RTreeGenerator

class TreeGeneratorFactory:
    def __init__(self, generator_name: str, extra_data: Dict):
        self.gen_name = generator_name
        self.extra_data = extra_data
        
    def get_generator(self) -> TreeGenerator:
        if self.gen_name == "python":
            return PythonTreeGenerator()
        elif self.gen_name == 'r':
            return RTreeGenerator()
        elif self.gen_name == "boba_python_template":
            return BobaPythonTemplateTreeGeneator(self.extra_data)
        elif self.gen_name == "boba_r_template":
            return BobaRTemplateGenerator(self.extra_data)
        else:
            raise NotImplementedError(f"generator: {self.gen_name} is not implemented")