
from src.gumtree.main.gen.tree_generator import PythonTreeGenerator

class TreeGeneratorFactory:
    def __init__(self, generator_name: str):
        self.gen_name = generator_name
        
    def get_generator(self):
        if self.gen_name == "python":
            return PythonTreeGenerator()
        else:
            raise NotImplementedError(f"generator: {self.gen_name} is not implemented")