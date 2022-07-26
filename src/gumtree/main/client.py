from src.gumtree.main.diff.diff import Diff
from src.gumtree.main.diff.io.action_io_utils import to_text


class TextDiff:
    DEFAULT_MATCHER = "classic"
    DEFAULT_GENERATOR = "python"
    def __init__(self, src_code, dst_code):
        self.src_code = src_code
        self.dst_code = dst_code
        self.generator = self.DEFAULT_GENERATOR
        self.matcher = self.DEFAULT_MATCHER

    def run(self):
        diff: Diff = self.get_diff()
        diff_str = str(to_text(diff.src, diff.edit_script, diff.mappings))
        print(diff_str)
        
    def get_diff(self):
        return Diff.compute_from_strs(self.src_code, self.dst_code, 
                               self.generator, self.matcher)
        
        
if __name__ == "__main__":
    FUNC1 = """
class Test:
    def foo(self, i):
        if i == 0:
            return "Foo!"
    """

    FUNC2 = """
class Test:
    def foo(self, i, j):
        if i == j:
            return "Bar"
        elif i == -1:
            return "Foo!"
    """
    
    client = TextDiff(FUNC1, FUNC2)
    client.run()