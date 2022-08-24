# -*- coding: utf-8 -*-
from __future__ import annotations
from copy import deepcopy

import json
import os
import pickle
from textwrap import wrap
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Tuple
from tqdm import tqdm
from src.gumtree.main.trees.tree import Tree

from .baseparser import ParseError
from .codeparser import CodeParser, Chunk, BlockCode
from .graphparser import GraphParser
from .graphanalyzer import GraphAnalyzer, InvalidGraphError
from .decisionparser import DecisionParser
from .constraintparser import ConstraintParser
from .lang import LangError, Lang
from .wrangler import Wrangler, DIR_SCRIPT
from .adg import ADG

import src.boba.util as util

@dataclass
class History:
    """
    A class for keeping track of the choices made in each universe.

    path: index of the code path.
    filename: file name of the universe.
    decisions: placeholder variables and the options they took.
    skipped: nodes that are skipped.
    """
    path: int
    filename: str = ''
    decisions: List[DecRecord] = field(default_factory=lambda: [])
    skipped: List = field(default_factory=lambda: [])

    @property
    def decision_dict(self) -> Dict[str, Tuple[str, int]]:
        return {dec_record.parameter: (dec_record.option, dec_record.idx) for dec_record in self.decisions}
        

@dataclass
class DecRecord:
    """ A class for what options a parameter took. """
    parameter: str = ''
    option: str = ''
    idx: int = -1

class Parser:

    """ Parse everything """

    def __init__(self, f1, out='.', lang=None, add_paren=False):
        self.fn_script = os.path.abspath(f1)
        with open(self.fn_script, 'r') as f:
            self.template_code = f.read()
        self.parent_dir = out
        self.out = os.path.join(out, 'multiverse/')

        self.paths = []
        self.history = []
        self.constraints = {}

        # init parser class
        self.code_parser = CodeParser()
        self.dec_parser = DecisionParser()
        self.adg = ADG()

        # parse
        self._parse_blocks()
        self.spec = self.code_parser.spec
        self._parse_decs()
        self._parse_graph()
        self._parse_constraints()

       

        self.universe_to_blocks = {}
        # init helper class
        try:
            supported_langs = None
            try:
                with open(os.path.join(self.parent_dir, self.spec['lang']), 'r') as l:
                    supported_langs = json.load(l)
            except KeyError:
                pass

            self.lang = Lang(f1, lang=lang, supported_langs=supported_langs)
            self.wrangler = Wrangler(self.spec, self.lang, self.out)
          
        except LangError as e:
            self._throw(e.args[0])
        except ParseError as e:
            self._throw_spec_error(e.args[0])
        
        self.paths_code = self.get_paths_code()
        self.add_paren = add_paren
        
         # ast related processing
        self.template_code_blocks: List[BlockCode] = self.code_parser.all_blocks
        
            
    
    def get_paths_code(self) -> List[str]:
        paths_code = []
        for path in self.paths: 
            strs = []
            for block_name in path:
                strs.append(self.code_parser.blocks[block_name].code_str)
            paths_code.append(''.join(strs))
        return paths_code
            
    def _throw(self, msg):
        util.print_fail(msg)
        exit(1)

    def _indent(self, msg):
        return '\n'.join(['\t' + l for l in msg.split('\n')])

    @staticmethod
    def _rename_dec(dec):
        return '_' + dec

    def _throw_parse_error(self, msg):
        prefix = 'In parsing file "{}":\n'.format(self.fn_script)
        self._throw(prefix + self._indent(msg))

    def _throw_spec_error(self, msg):
        prefix = 'In parsing boba config:\n' + json.dumps(self.spec) + '\n'
        self._throw(prefix + self._indent(msg))

    def _parse_blocks(self):
        """ Make a pass over the template, parsing block declarations and
        placeholder variables inside the code."""
        with open(self.fn_script, 'r') as f:
            try:
                self.code_parser.parse(self.dec_parser, f)
            except ParseError as e:
                self._throw_parse_error(e.args[0])

    def _parse_decs(self):
        """ Parse decisions in the spec. """
        try:
            self.dec_parser.read_decisions(self.spec)
        except ParseError as e:
            self._throw_spec_error(e.args[0])

        # check if used variables has been declared
        for v in self.code_parser.used_vars:
            if v not in set(self.dec_parser.decisions.keys()):
                msg = 'Cannot find matching variable "{}" in spec'.format(v)
                self._throw_spec_error(msg)

    def _match_nodes(self, nodes):
        """ Nodes in spec and script should match. """
        blocks = self.code_parser.get_block_names()

        for nd in nodes:
            if nd not in blocks:
                self._throw_spec_error('Cannot find matching node "{}" in script'.format(nd))

        for nd in blocks:
            # ignore special nodes inserted by us
            if not nd.startswith('_') and nd not in nodes:
                util.print_warn('Cannot find matching node "{}" in graph spec'.format(nd))

    def _parse_graph(self):
        graph_spec = self.spec['graph'] if 'graph' in self.spec else []

        try:
            gp = GraphParser(graph_spec)
            nodes, edges = gp.parse()

            # if the user didn't specify the graph, use default
            if len(nodes) == 0:
                nodes, edges = gp.create_default_graph(self.code_parser.order)

            # check if graph nodes matches block IDs, and vice versa
            self._match_nodes(nodes)
            # check if any name of nodes collides with variable names
            self.dec_parser.verify_naming(nodes)
            # expand the graph with options
            nodes, edges = gp.replace_graph(self.code_parser.get_decisions())

            # analyze the graph to get paths
            self.paths = GraphAnalyzer(nodes, edges).analyze()
    
            # an ugly way to handle the artificial _start node
            if '_start' in self.code_parser.blocks and '_start' not in nodes:
                for p in self.paths:
                    p.insert(0, '_start')
                if len(self.paths) == 0:
                    self.paths = [['_start']]

            # save data to adg
            self.adg.set_graph(nodes, edges)
        except ParseError as e:
            self._throw_spec_error(e.args[0])
        except InvalidGraphError as e:
            self._throw_spec_error(e.args[0])

    def _parse_constraints(self):
        try:
            cp = ConstraintParser(self.spec)
            self.constraints = cp\
                .read_constraints(self.code_parser, self.dec_parser)
            # save intermediate data for ADG
            self.adg.set_constraints(cp.links, cp.procedural)
        except ParseError as e:
            self._throw_spec_error(e.args[0])

    def _eval_constraint(self, history, con):
        """ See if the constraint holds true given the choices made. """
        con = self.constraints[con].condition
        paths, bdecs = self._nice_path(self._get_skipped_path(history))

        # A dict where the key is each parameter and the value is the chosen
        # option. For ordinary blocks, key and value are the same.
        res = {}
        for p in paths:
            res[p] = p
        for d in bdecs:
            # note that block parameter will override with the actual option
            res[d.parameter] = d.option
        for d in self.dec_parser.get_decs():
            # unmade decisions will have value None and index -1
            res[d] = None
            res[ConstraintParser.make_index_var(d)] = -1
        for d in history.decisions:
            res[d.parameter] = d.option
            res[ConstraintParser.make_index_var(d.parameter)] = d.idx

        # now evaluate
        return eval(con, res)

    def _get_code_paths(self):
        """ Convert paths of block to paths of code chunk """

        res = []

        for path in self.paths:
            pt = []
            for nd in path:
                # replace the node by its chunks
                chunks = [(nd, ch) for ch in self.code_parser.blocks[nd].chunks]
                pt.extend(chunks)
            res.append(pt)

        return res
    # @profile
    def _code_gen_recur(self, 
                        path: List[Tuple[str, Chunk]], 
                        path_block_changes: List[Tuple[str, int, int]], 
                        p_i: int, 
                        pbc_i: int, 
                        code: str, 
                        cur_block_code: str, 
                        history: History,
                        block_codes: List[BlockCode]):
        """
        Generate code recursively.

        :param path: the code path we're on.
        :param i: the index of the current node in the code path.
        :param code: the generated code so far.
        :param history: record the choices made.
        """

        if p_i >= len(path): #base case
            # write file
            
            fn, code, cur_block_code = self.wrangler.write_universe(code, cur_block_code)

            # record history
            history.filename = fn
            self.history.append(history)
            block_codes  = block_codes + [BlockCode(dec_name=path_block_changes[pbc_i][0].split(':')[0],
                                         opt_name=path_block_changes[pbc_i][0].split(':')[-1],
                                         code_length=cur_block_code.count('\n') + 1
                                        )]
            # block_codes[0].code_length += 1
            assert sum(b.code_length for b in block_codes) == len(code.split('\n'))
            self.blocks_code.append(block_codes)
        else:
            if p_i == path_block_changes[pbc_i][2]:
                block_codes = block_codes + [BlockCode(
                    dec_name=path_block_changes[pbc_i][0].split(':')[0],
                    opt_name=path_block_changes[pbc_i][0].split(':')[-1],
                    code_length=cur_block_code.count('\n')
                )]
                pbc_i += 1
                cur_block_code = ''
            
            nd, chunk = path[p_i]

            # check if the block has constraints attached to it
            names = [nd, nd.split(':')[0]]
            for n in names:
                if n in self.constraints and\
                        not self._eval_constraint(history, n):
                    # constraint met
                    if self.constraints[n].skip:
                        # skip the node and continue
                        history.skipped.append(nd)
                        self._code_gen_recur(path, 
                                             path_block_changes,
                                             p_i + 1, 
                                             pbc_i,
                                             code, 
                                             cur_block_code, 
                                             history,
                                             block_codes)
                        return
                    else:
                        # abort codegen
                        return

            if chunk.variable != '':
                # check if we have already encountered the placeholder variable
                prev_idx = None
                for d in history.decisions:
                    if d.parameter == chunk.variable:
                        prev_idx = d.idx

                if prev_idx is not None:
                    # use the previous value
                    # if chunk.variable.startswith('_'):
                    #     snippet = chunk.code + '{{' + chunk.variable + '}}'
                    #     self._code_gen_recur(path, 
                    #                      path_block_changes,
                    #                      p_i + 1, 
                    #                      pbc_i,
                    #                      code + snippet, 
                    #                      cur_block_code + snippet, 
                    #                      history,
                    #                      block_codes)
                    snippet, opt = self.dec_parser.gen_code(chunk.code, chunk.variable, prev_idx, add_paren=self.add_paren)
                    self._code_gen_recur(path, 
                                         path_block_changes,
                                         p_i + 1, 
                                         pbc_i,
                                         code + snippet, 
                                         cur_block_code + snippet, 
                                         history,
                                         block_codes)
                else:
                    # expand the decision
                    if chunk.variable.startswith('_'):
                        snippet = chunk.code + '{{' + chunk.variable + '}}'
                        # decs = [a for a in history.decisions]
                        # decs.append(DecRecord(chunk.variable, -1, -1))
                        self._code_gen_recur(path,
                                             path_block_changes,
                                             p_i + 1,
                                             pbc_i,
                                             code + snippet,
                                             cur_block_code + snippet,
                                             history,
                                             deepcopy(block_codes)
                                             )
                    else:
                        num_alt = self.dec_parser.get_num_alt_discrete(chunk.variable)
                        for k in range(num_alt):
                            # check if the option has constraints attached to it
                            # always check by index, rather than actual value
                            v = ConstraintParser.make_index_var(chunk.variable)
                            v = '{}:{}'.format(v, k)
                            if v in self.constraints and \
                                    not self._eval_constraint(history, v):
                                # constraint met, abort
                                continue

                            # code gen
                            snippet, opt = self.dec_parser.gen_code(chunk.code, chunk.variable, k, add_paren=self.add_paren)
                            decs = [a for a in history.decisions]
                            decs.append(DecRecord(chunk.variable, opt, k))
                            self._code_gen_recur(path, 
                                                path_block_changes, 
                                                p_i + 1, 
                                                pbc_i,
                                                code + snippet, 
                                                cur_block_code + snippet,
                                                History(history.path, '', decs),
                                                deepcopy(block_codes))
            else:
                code += chunk.code
                cur_block_code += chunk.code
                self._code_gen_recur(path, path_block_changes, p_i+1, pbc_i, code, cur_block_code,
                                     history, block_codes)

    def _code_gen(self):
        paths = self._get_code_paths()
        def get_path_block_changes(paths) -> List[Tuple[str, int, int]]:  
            paths_block_change_idxs = []
            for path in paths:
                path_block_changes = []
                cur_block_name = path[0][0]
                cur_block_start = 0
                cur_var = path[0][1].variable
                for ind, path_step in enumerate(path[1:]):
                    if path_step[0] == cur_block_name and not (cur_var == ''):
                        continue
                    else:
                        path_block_changes.append((cur_block_name, cur_block_start, ind+1))
                        cur_block_name = path_step[0]
                        cur_block_start = ind + 1
                    cur_var = path_step[1].variable
                path_block_changes.append((cur_block_name, cur_block_start, len(path)))
                paths_block_change_idxs.append(path_block_changes)
            return paths_block_change_idxs
        path_block_changes = get_path_block_changes(paths)   

        self.wrangler.counter = 0  # keep track of file name
        self.history = []          # keep track of choices made for each file
        self.blocks_code = []
        self.wrangler.col = 2 + len(self.dec_parser.get_decs())\
            + len(self.code_parser.get_decisions())

        self.wrangler.create_dir()
        with tqdm() as pbar:
            self.wrangler.pbar = pbar
            for idx, (p, pbc) in enumerate(zip(paths, path_block_changes)):
                self._code_gen_recur(p, pbc, 0, 0, '', '', History(idx), [])
        self.wrangler.pbar = None
        # write the pre and post execs to a file.
        self.wrangler.write_pre_exe()
        self.wrangler.write_post_exe()
        self.wrangler.write_lang()

    @staticmethod
    def _nice_path(path):
        """ Convert the path containing block options back to the simpler path
         containing only block parameters."""
        ps = [p.split(':')[0] for p in path]
        decs = [DecRecord(p.split(':')[0], p.split(':')[1]) for p in path if ':' in p]
        return ps, decs

    def _get_skipped_path(self, h):
        """ Get the history's path, with skipped nodes removed. """
        sk = set(h.skipped)
        return [nd for nd in self.paths[h.path] if nd not in sk]

    def _write_csv(self):
        rows = []
        decs = self.dec_parser.get_decs() +\
            [b for b in self.code_parser.get_decisions()]
        ops = self.wrangler.get_outputs()
        rows.append(['Filename', 'Code Path'] + decs + ops)
        for h in self.history:
            paths, bdecs = self._nice_path(self._get_skipped_path(h))
            row = [h.filename, '->'.join(paths)]
            mp = {}
            for d in h.decisions:
                mp[d.parameter] = d.option
            for d in bdecs:
                mp[d.parameter] = d.option
            for d in decs:
                value = mp[d] if d in mp else ''
                row.append(value)
            rows.append(row)
        self.wrangler.write_summary(rows)

    def _write_server_config(self):
        self.adg.create(self.code_parser.blocks)
        res = self.adg.output()

        # get the options of decision blocks and placeholders
        lookup = self.code_parser.get_decisions()
        for d in lookup:
            lookup[d] = [v.split(':')[1] for v in lookup[d]]
        decs = self.dec_parser.decisions
        for d in decs:
            lookup[d] = decs[d].value

        # now wrangle the decisions
        decs = self.adg.get_used_decs()
        decs = [{"var": d, "options": lookup[d]} for d in decs]
        res["decisions"] = decs

        # save
        self.wrangler.write_overview_json(res)

    def _print_summary(self):
        w = 80
        max_rows = 10

        print('=' * w)
        print('{:<20}{:<30}{:<30}'.format('Filename', 'Code Path', 'Decisions'))
        print('=' * w)
        for idx, h in enumerate(self.history):
            paths, bdecs = self._nice_path(self._get_skipped_path(h))
            path = wrap('->'.join(paths), width=27)
            decs = ['{}={}'.format(d.parameter, d.option) for d in bdecs + h.decisions]
            decs = wrap(', '.join(decs), width=30)
            max_len = max(len(decs), len(path))

            for r in range(max_len):
                c1 = h.filename if r == 0 else ''
                c2 = path[r] if r < len(path) else ''
                c3 = decs[r] if r < len(decs) else ''

                print('{:<20}'.format(c1), end='')
                print('{:<30}'.format(c2), end='')
                print('{:<30}'.format(c3))
            print('-' * w)

            if idx >= max_rows - 1:
                print('... {} more rows'.format(len(self.history) - max_rows))
                break

    def _warn_size(self):
        cap = self.dec_parser.get_cross_prod_discrete() * len(self.paths)
        if cap > 1024:
            rs = input('\nBoba may create as many as {} scripts. '
                       'Proceed (y/n)?\n'.format(cap))
            if not rs.strip().lower().startswith('y'):
                print('Aborted.')
                exit(0)
    
    def _save_parser(self):
        out_folder = os.path.join(self.out, DIR_SCRIPT, ".boba_parser")
        os.makedirs(out_folder)
        out_file = os.path.join(out_folder, 'parser.pickle')
        with open(out_file, 'wb') as f:
            pickle.dump(self, f)

    def main(self, verbose=True):
        self._warn_size()
        self._code_gen()
        self._write_csv()
        self._write_server_config()
        if verbose:
            self._print_summary()
        self._save_parser()

    def main_wo_warning(self, verbose=True):
        self._code_gen()
        self._write_csv()
        self._write_server_config()
        if verbose:
            self._print_summary()
        self._save_parser()