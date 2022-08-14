import click
import os.path as osp
import pickle
from src.gui import app_diff, app_error_dashboard
from src.gui.monaco_diff import TemplateDiffView
from src.aggregate_error import DebugMultiverse

from src.gui import routes_diff, routes_error

def diff_helper(universe_path):
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


@click.command()
@click.argument('universe_path', type=click.Path(exists=True))
@click.option('--port', default=8080, show_default=True,
              help='The port to bind the server to')
@click.option('--host', default='0.0.0.0', show_default=True,
              help='The interface to bind the server to')
@click.version_option()
def diff_gui(universe_path, port, host):
    app_diff.diff_view = diff_helper(universe_path)
    # s_host = '127.0.0.1' if host == '0.0.0.0' else host
    msg = """\033[92m
    Server started!
    Navigate to http://{0}:{1}/ in your browser
    Press CTRL+C to stop\033[0m""".format(host, port)
    print(msg)
    
    app_diff.run(host=host, port=f'{port}') 
    app_diff.config['TEMPLATES_AUTO_RELOAD'] = True
    

@click.command()
@click.option('--in', '-i', 'folder', default='.', type=click.Path(exists=True),
              show_default=True, help='Path to the input directory, the multiverse folder')
@click.option('--port', default=8070, show_default=True,
              help='The port to bind the server to')
@click.option('--host', default='0.0.0.0', show_default=True,
              help='The interface to bind the server to')
@click.version_option()
def error_aggr_gui(folder, port, host):
    app_error_dashboard.data_folder = osp.realpath(folder)
    app_error_dashboard.aggr_error = DebugMultiverse(app_error_dashboard.data_folder)
    app_error_dashboard.run(host=host, port=f'{port}') 


@click.group()
def main():
    pass

main.add_command(diff_gui, "diff")
main.add_command(error_aggr_gui, "error")


if __name__ == "__main__":
    main()