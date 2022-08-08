from src.gui import app
from src.gui import routes

from src.gui.monaco_diff import TemplateDiffView


if __name__ == "__main__":
    from src.utils import load_parser_example, DATA_DIR
    import os.path as osp
    dataset, ext = 'fertility2', 'py'
    save_file = osp.join(DATA_DIR, f'{dataset}_template_parser_obj_0804.pickle')
    ps = load_parser_example(dataset, ext, save_file, run_parser_main=True)
    tdv = TemplateDiffView(ps, osp.join(DATA_DIR, dataset, 'multiverse', 'code', 'universe_3.py'))
    app.diff_view = tdv
    app.run()