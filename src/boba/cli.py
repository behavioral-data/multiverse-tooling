# -*- coding: utf-8 -*-

"""Console script."""
import click
import shutil
import os
import os.path as osp
import pandas as pd
import pickle
from src.boba.parser import Parser
from src.boba.output.csvmerger import CSVMerger
from src.boba.bobarun import BobaRun
from src.aggregate_error import get_min_decisions
from src.gui import app_diff, app_error_dashboard
from src.gui.monaco_diff import TemplateDiffView
from src.aggregate_error import DebugMultiverse

from src.gui import routes_diff, routes_error

@click.command()
@click.option('--script', '-s', help='Path to template script',
              default='./template.py', show_default=True)
@click.option('--out', help='Output directory',
              default='.', show_default=True)
@click.option('--lang', help='Language, can be python/R [default: inferred from file extension]',
              default=None)
def compile(script, out, lang):
    """Generate multiverse analysis from specifications."""

    check_path(script)

    click.echo('Creating multiverse from {}'.format(script))
    ps = Parser(script, out, lang)
    ps.main()

    ex = """To execute the multiverse, run the following commands:
    boba run --all
    """.format(os.path.join(out, 'multiverse'))
    click.secho('Success!', fg='green')
    click.secho(ex, fg='green')


def check_path(p):
    """Check if the path exists"""
    if not os.path.exists(p):
        msg = 'Error: Path "{}" does not exist.'.format(p)
        print_help(msg)


def print_help(err=''):
    """Show help message and exit."""
    ctx = click.get_current_context()
    click.echo(ctx.get_help())

    if err:
        click.echo('\n' + err)
    ctx.exit()


@click.command()
@click.argument('num', nargs=1, default=-1)
@click.option('--all', '-a', 'run_all', is_flag=True,
              help='Execute all universes')
@click.option('--thru', default=-1, help='Run until this universe number')
@click.option('--jobs', default=1, help='The number of universes that can be running at a time.')
@click.option('--batch_size', default=0, help='The approximate number of universes a processor will run in a row.')
@click.option('--dir', 'folder', help='Multiverse directory',
              default='./multiverse', show_default=True)
@click.option('--cover_check', is_flag=True, show_default=True, default=False, help="Whether to run the min cover as a sanity check")
def run(folder, run_all, num, thru, jobs, batch_size, cover_check):
    """ Execute the generated universe scripts.

    Run all universes: boba run --all

    Run a single universe, for example universe_1: boba run 1

    Run a range of universes for example 1 through 5: boba run 1 --thru 5
    """

    check_path(folder)

    df = pd.read_csv(folder + '/summary.csv')
    num_universes = df.shape[0]

    if not run_all and not cover_check:
        if thru == -1:
            thru = num
        if num < 1:
            print_help()
        if thru < num:
            print_help('The thru parameter cannot be less than the num parameter.')
        if num > num_universes or thru > num_universes:
            print_help(f'There are only {num_universes} universes.')
            
    if cover_check:
        min_decs = get_min_decisions(df)
        print(f"Running minimum universes, {len(min_decs)} of {len(df)}")
        br = BobaRun(folder, jobs, batch_size)
        for universe_num in min_decs.keys():
            br.run_from_cli(False, universe_num, -1)
        app_error_dashboard.data_folder = osp.realpath(folder)
        app_error_dashboard.aggr_error = DebugMultiverse(app_error_dashboard.data_folder)
        app_error_dashboard.run(host='0.0.0.0', port=f'8060')
    else:
        br = BobaRun(folder, jobs, batch_size)
        br.run_from_cli(run_all, num, thru)


@click.command()
@click.argument('pattern', nargs=1)
@click.option('--base', '-b', default='./multiverse/results',
              show_default=True, help='Folder containing the universe outputs')
@click.option('--out', default='./multiverse/merged.csv',
              show_default=True, help='Name of the merged file')
@click.option('--delimiter', default=',', show_default=True,
              help='CSV delimiter')
def merge(pattern, base, out, delimiter):
    """
    Merge CSV outputs from individual universes into one file.

    Required argument:
    the filename pattern of individual outputs where the universe id is
    replaced by {}, for example output_{}.csv
    """

    check_path(base)
    CSVMerger(pattern, base, out, delimiter).main()


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
@click.option('--in', '-i', 'folder', default='./multiverse', type=click.Path(exists=True),
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
@click.version_option()
def main():
    pass


main.add_command(compile)
main.add_command(run)
main.add_command(merge)
main.add_command(diff_gui, "diff")
main.add_command(error_aggr_gui, "error")

if __name__ == "__main__":
    main()
