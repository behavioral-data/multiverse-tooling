import click
import os.path as osp
import pickle
from src.gui import app, routes
from src.gui.monaco_diff import TemplateDiffView


@click.command()
@click.argument('universe_path', type=click.Path(exists=True))
@click.option('--port', default=8080, show_default=True,
              help='The port to bind the server to')
@click.option('--host', default='0.0.0.0', show_default=True,
              help='The interface to bind the server to')
@click.version_option()
def main(universe_path, port, host):
    
    app.diff_view = main_helper(universe_path)
    # s_host = '127.0.0.1' if host == '0.0.0.0' else host
    msg = """\033[92m
    Server started!
    Navigate to http://{0}:{1}/ in your browser
    Press CTRL+C to stop\033[0m""".format(host, port)
    print(msg)
    
    app.run(host=host, port=f'{port}') 
    
def main_helper(universe_path):
    universe_path = osp.realpath(universe_path)
    print(universe_path)
    dir_code = osp.dirname(universe_path)
    parser_pickle_path = osp.join(dir_code, '.boba_parser', 'parser.pickle')
    if not osp.exists(parser_pickle_path):
        print('Cached boba parser does not exist. Could not run bdiff')
        return
    with open(parser_pickle_path, 'rb') as f:
        ps = pickle.load(f)
    print('Calculating Diff ...')
    template_diff_view = TemplateDiffView(ps, universe_path)
    return template_diff_view

if __name__ == "__main__":
    main()