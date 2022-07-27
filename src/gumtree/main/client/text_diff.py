
from src.gumtree.main.client.client import Client
from src.gumtree.main.diff.diff import Diff
from src.gumtree.main.diff.io.action_io_utils import to_json, to_text


class TextDiff(Client):
    
    def __init__(self, src_code, dst_code, configurations):
        super().__init__(src_code, dst_code)
        self.configurations = {} if configurations is None else configurations
        self.configure()
        
    def configure(self, configurations=None):
        configurations = self.configurations if configurations is None else configurations
        self.formatter = configurations.get("formatter", "text")
        super().configure(configurations)
        
    def run(self):
        diff: Diff = self.get_diff()
        if self.formatter == "text":
            diff_str = str(to_text(diff.src, diff.edit_script, diff.mappings))
        elif self.formatter == "json":
            diff_str = str(to_json(diff.src, diff.edit_script, diff.mappings))
        return diff_str

if __name__ == "__main__":
    from src.utils import load_parser_example, read_universe_file, VIZ_DIR, DATA_DIR
    import os.path as osp
    from src.utils import save_viz_code_pdf
    from src.gumtree.main.client.dot_diff import DotDiff
    
    dataset, ext = 'fertility', 'py'
    save_file = osp.join(DATA_DIR, f'{dataset}_template_parser_obj_0718.pickle')
    ps = load_parser_example(dataset, ext, save_file)
    universe_num = 3
    template_code = ps.paths_code[ps.history[universe_num - 1].path]
    universe_code = read_universe_file(universe_num, dataset, ext)
    configurations = {
        "formatter": "text",
        "generator": ("boba_python_template", "python"),
        "matcher": "boba",
        "parser_history": ps.history[universe_num - 1]
    }
    
    TEMPLATE_CODE = """
cl = df.last_period_start - df.period_before_last_start 
df.loc[df.relationship <= {{relationship_bounds}}[0],
                'relationship_status'] = 'Single'
df.loc[df.relationship >= {{relationship_bounds}}[1],
                'relationship_status'] = 'Relationship'
    """
    
    
    
    PYTHON_CODE = """
df.loc[df.relationship <= 2 + [2, 5][0],
                'relationship_status'] = 'Single'
df.loc[df.relationship >= [2, 3][1],
                'relationship_status'] = 'Relationship'
    """
    # save_viz_code_pdf(TEMPLATE_CODE, osp.join(VIZ_DIR, "template_ex.pdf"))
    # save_viz_code_pdf(PYTHON_CODE, osp.join(VIZ_DIR, "universe_ex.pdf"))
    
    # diff = TextDiff(template_code, template_code, configurations=configurations)
    # res = diff.run()
    
    dot_client = DotDiff(template_code, universe_code, configurations=configurations)
    
    save_path = osp.join(VIZ_DIR, "diff_universe_template.dot")
    dot_client.save_diff_to_file(save_path)
    
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
    
    client = TextDiff(FUNC1, FUNC2, {"formatter": "json"})
    s1 = client.run()