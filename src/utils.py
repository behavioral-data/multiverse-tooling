import logging
import json
from typing import Union
from os.path import dirname, abspath, join, exists
from src.ast_viz import viz_code
from src.boba.parser import Parser
import pickle 

PROJECT_ROOT_DIR = dirname(dirname(abspath(__file__)))
DATA_DIR = join(PROJECT_ROOT_DIR, 'data')
SRC_DIR = join(PROJECT_ROOT_DIR, 'src')
VIZ_DIR = join(PROJECT_ROOT_DIR, 'visualizations')
OUTPUT_DIR = join(PROJECT_ROOT_DIR, 'output')

def get_logger(name):
    logger = logging.getLogger(name)
    logging.basicConfig(
        forloggmat="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=logging.INFO
    )
    return logger

def save_viz_code_pdf(code, save_path):
    svg, graph = viz_code(code)
    with open(save_path, 'wb') as f:
        f.write(graph.pipe(format='pdf'))

def load_parser_example(dataset: str, ext: str, save_file=None,
                        run_parser_main=False) -> Parser:
    script = join(DATA_DIR, dataset, f'template.{ext}')
    out = join(DATA_DIR, dataset)
    ps = Parser(script, out, None)
    
    if save_file is None:
        if run_parser_main:
            ps.main()
        return ps
    
    if not exists(save_file):
        ps.main()
        with open(save_file, 'wb') as f:
            pickle.dump(ps, f)
    with open(save_file, 'rb') as f:
        ps = pickle.load(f)
    return ps

def read_universe_file(universe_num, dataset, ext='py'):
    universe_code_dir = join(DATA_DIR, dataset, 'multiverse', 'code')
    universe_path = join(universe_code_dir, f'universe_{universe_num}.{ext}')
    with open(universe_path, 'r') as f:
        universe_code = f.read()
    return universe_code
    

class CompactJSONEncoder(json.JSONEncoder):
    """A JSON Encoder that puts small containers on single lines."""

    CONTAINER_TYPES = (list, tuple, dict)
    """Container datatypes include primitives or other containers."""

    MAX_WIDTH = 70
    """Maximum width of a container that might be put on a single line."""

    MAX_ITEMS = 2
    """Maximum number of items in container that might be put on single line."""

    INDENTATION_CHAR = " "

    def __init__(self, *args, **kwargs):
        # using this class without indentation is pointless
        if kwargs.get("indent") is None:
            kwargs.update({"indent": 4})
        super().__init__(*args, **kwargs)
        self.indentation_level = 0
    
    def encode(self, o):
        """Encode JSON object *o* with respect to single line lists."""
        if isinstance(o, (list, tuple)):
            if self._put_on_single_line(o):
                return "[" + ", ".join(self.encode(el) for el in o) + "]"
            else:
                self.indentation_level += 1
                output = [self.indent_str + self.encode(el) for el in o]
                self.indentation_level -= 1
                return  "[\n" + ",\n".join(output) + "\n" + self.indent_str + "]" 
        elif isinstance(o, dict):
            if o:
                if self._put_on_single_line(o):
                    return "{ " + ", ".join(f"{self.encode(k)}: {self.encode(el)}" for k, el in o.items()) + " }"
                else:
                    self.indentation_level += 1
                    output = [self.indent_str + f"{json.dumps(k)}: {self.encode(v)}" for k, v in o.items()]
                    self.indentation_level -= 1
                    return "{\n" + ",\n".join(output) + "\n" + self.indent_str + "}"
            else:
                return "{}"
        elif isinstance(o, float):  # Use scientific notation for floats, where appropiate
            return format(o, "g")
        elif isinstance(o, str):  # escape newlines
            o = o.replace("\n", "\\n")
            return f'"{o}"'
        else:
            return json.dumps(o)

    def iterencode(self, o, **kwargs):
        """Required to also work with `json.dump`."""
        return self.encode(o)

    def _put_on_single_line(self, o):
        return self._primitives_only(o) and len(o) <= self.MAX_ITEMS and len(str(o)) - 2 <= self.MAX_WIDTH

    def _primitives_only(self, o: Union[list, tuple, dict]):
        if isinstance(o, (list, tuple)):
            return not any(isinstance(el, self.CONTAINER_TYPES) for el in o)
        elif isinstance(o, dict):
            return not any(isinstance(el, self.CONTAINER_TYPES) for el in o.values())

    @property
    def indent_str(self) -> str:
        return self.INDENTATION_CHAR*(self.indentation_level*self.indent)

if __name__ == '__main__':
    print(PROJECT_ROOT_DIR)