from copy import deepcopy
from collections import defaultdict
from pickle import TRUE
from typing import Dict, FrozenSet, Set, List, Tuple
import pandas as pd
import glob
from os.path import join
from pathlib import Path
import difflib
from pprint import pprint
import yaml
import random

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def frozen_set_to_str(fr_set_tup, orig_decision_dict):
    orig_dict = {}
    for tup in fr_set_tup:
        key, val = tup
        if val == orig_decision_dict[key]:
            continue
        orig_dict[tup[0]] = list(tup[1])
    
    if not orig_dict:
        return 'All Universes'
    return yaml.dump(orig_dict)

def get_decs(summary_df) -> Dict[str, list]:
    return {c : frozenset(summary_df[c].unique())
            for c in summary_df.columns[2:]}
    


    
def set_universe_as_index(summary_df):
    summary_df['universe_num'] = summary_df['Filename'].apply(lambda x: int(x.split('_')[-1].split('.')[0]))
    return summary_df.set_index('universe_num')

class DebugMultiverse:
    def __init__(self, log_folder, df: pd.DataFrame):
        self.log_folder = log_folder
        self.summary_df = df.fillna('')
        decisions = get_decs(self.summary_df)
        self._decisions = {k: v for k, v in decisions.items() if len(v) > 1}
        self._unum_shared_lines, self._decisions_to_lines, self._common_lines = self.init_debug_multiverse() 
        self._lines_to_decisions = {line: k for k, v in self.decisions_to_lines.items() for line in v}

    @property
    def orig_decisions(self) -> Dict[str, FrozenSet[str]]:
        """
        Mapping from decisions name to its decision options
        """
        return self._decisions
    
    @property
    def unum_shared_lines(self) -> Dict[int, Dict[str, Set[int]]]:
        """
        Mapping from unum to a Dict mapping its associated code lines to a set of other universes that 
        share that code.
        Has length number of universes
        """
        return self._unum_shared_lines
    
    @property
    def decisions_to_lines(self) -> Dict[Tuple[Tuple[str, FrozenSet[str]]], List[str]]:
        """
        Mapping from a set of decision and options to the code lines which these decisions and options share:
        
        Example key:
            (   
                ('M', frozenset({'negative_binomial'})),
                ('covariate_list', frozenset({''})),
                ('covariates', frozenset({'', '+ post:damage', '+ year:damage'})),
                ('damage', frozenset({'log_dam', 'dam'})),
                ('feminity', frozenset({'female', 'masfem'})),
                ('outliers',
                frozenset({"c('Katrina')",
                            "c('Katrina', 'Audrey')",
                            "c('Katrina', 'Audrey', 'Sandy')",
                            "c('Katrina', 'Audrey', 'Sandy', 'Andrew')",
                            "c('Katrina', 'Audrey', 'Sandy', 'Andrew', 'Donna')",
                            'c()'})),
                ('predictor_list', frozenset({''})),
                ('predictors',
                frozenset({'feminity + damage + pressure + feminity:damage + '
                            'feminity:pressure',
                            'feminity + damage + z3',
                            'feminity + damage + z3 + feminity:damage + feminity:z3',
                            'feminity + damage + zcat + feminity:damage + feminity:zcat',
                            'feminity + damage + zwin + feminity:damage + feminity:zwin'})),
                ('undo_transform', frozenset({'exp(value)'}))
            )
        """
        return self._decisions_to_lines
    
    @property
    def common_lines(self) -> Dict[FrozenSet[int], List[str]]:
        """
        Mapping from set of universe nums to lines of code in which all these universes share
        """
        return self._common_lines
    @property
    def lines_to_decisions(self) -> Dict[str, Tuple[Tuple[str, FrozenSet[str]]]]:
        """
        Mapping from line of code to the decisions and options which share this code
        """
        return self._lines_to_decisions
    
    
    def init_debug_multiverse(self):
        log_folder = self.log_folder
        summary_df = self.summary_df
        res = defaultdict(list)
        res_lines = defaultdict(set)
        for p in Path(log_folder).glob('error*.txt'):
            universe_num = int(p.name.split('_')[-1].split('.')[0])
            res[p.read_text()].append(universe_num)
            for line in p.read_text().split('\n'):
                res_lines[line].add(universe_num)
        def get_common_lines(res_lines: Dict[str, set]):
            new_res = defaultdict(list)
            for line, unum_set in res_lines.items():
                key = frozenset(unum_set)
                new_res[key].append(line)
            return new_res
        common_lines  = get_common_lines(res_lines)
        summary_df = set_universe_as_index(summary_df)
        summary_df.fillna('', inplace=True)
        
        decisions_to_lines = defaultdict(list)
        for k, line in common_lines.items():
            subset_df = summary_df.loc[list(k)]
            decisions = get_decs(subset_df)
            decisions = {k: v for k, v in decisions.items() if k in self.orig_decisions}
            decisions_repr = tuple((k, decisions[k])for k in sorted(decisions.keys())) 
            decisions_to_lines[decisions_repr].append('\n'.join(line))
        unum_shared_lines: Dict[int, Dict[str, Set[int]]] = defaultdict(dict)
        
        for k, lines in common_lines.items():
            for unum in k:
                shared_unums = set(k)
                shared_unums.discard(unum)
                unum_shared_lines[unum]['\n'.join(lines)] = shared_unums
    
        return unum_shared_lines, decisions_to_lines, common_lines

    def print_common_universes(self, unum):
        """
        For a universe what are its error ouputs and what are some other sample universes associated with its error output
        """
        print(f'{bcolors.OKGREEN} ====== Universe {unum} Common Code Universes======')
        for lines, other_unums in self.unum_shared_lines[unum].items():
            print(f'{bcolors.OKBLUE}{lines}')
            print(f'{bcolors.OKGREEN}Shared unums: {random.sample(list(other_unums), 10)}')
            print(f'{bcolors.OKGREEN}Total shared: {len(other_unums)}\n\n')
        
    def print_common_output(self, unum1, unum2):
        """
        What are common error outputs between universe A and universe B
        """
        print(f'{bcolors.OKGREEN} ====== Universe {unum1} and {unum2} Common Code ======')
        for lines, other_nums in self.unum_shared_lines[unum1].items():
            if unum2 in other_nums:
                print(f'{bcolors.OKBLUE}{lines}')

    def print_decision_and_code(self, i=0):
        """
        What are some of the common error outputs and the associated decision with that error output
        """
        for ind, (k, lines) in enumerate(self.decisions_to_lines.items()):
            if ind == i:
                print(f'{bcolors.OKGREEN}======== Decisions ========{bcolors.OKGREEN}')
                print(frozen_set_to_str(k, self.orig_decisions))
                print(F'{bcolors.OKBLUE}======== Code ========{bcolors.OKBLUE}')
                print(f'\n\n'.join(lines))
        
    def print_common_decisions(self, unum):
        """
        For a universe what are the decisions associated with its error output
        What are also some other sample universes associated with its error output
        """
        print(f'{bcolors.OKGREEN}======== {unum} Code Decisions ========{bcolors.OKGREEN}')
        for lines, other_unums in self.unum_shared_lines[unum].items():
            decision = self.lines_to_decisions[lines]
            print(f'{bcolors.OKBLUE}====== Code ======{bcolors.OKBLUE}')
            print(lines)
            print(f'{bcolors.OKGREEN}====== Decisions ======{bcolors.OKGREEN}')
            print(f'{bcolors.OKGREEN}{frozen_set_to_str(decision, self.orig_decisions)}')
            print(f'{bcolors.OKGREEN}Sample shared unums: {random.sample(list(other_unums), 10)}')
            print(f'{bcolors.OKGREEN}Total shared: {len(other_unums)}\n\n')

    # TODO what are common decisions shared by two universes
def get_min_decisions(summary_df: pd.DataFrame):
    decision_options_dict: Dict[str, list] = {c: list(summary_df[c].unique())
                                                  for c in summary_df.columns[2:]}
    decision_options_dict = {k: set(v) for k, v in decision_options_dict.items() if len(v) > 1}
    summary_df = set_universe_as_index(summary_df)
    copy_df = deepcopy(summary_df)
    to_run = {}
    
    while len(copy_df) > 0 and any(len(v) > 0 for v in decision_options_dict.values()):
        row = copy_df.sample(1)
        to_run[row.index.values[0]] = {c: row[c].values[0] for c in row.columns[2:]}
        cols = [(c, copy_df[c].nunique()) 
                for c in copy_df.columns[2:] if copy_df[c].nunique() > 1]
        max_col = sorted(cols, key=lambda x: x[1])[-1][0]
        for col, v in decision_options_dict.items():
            v.discard(row[col].values[0])  
        copy_df = copy_df.loc[copy_df[max_col] != row[max_col].values[0]]
        
    return to_run

        
if __name__ == '__main__':
    from os.path import join
    MULTIVERSE_FOLDER = "/projects/bdata/kenqgu/Research/MultiverseProject/MultiverseTooling/multiverse-tooling/exploration/hurricane/boba_multiverse2"
    LOG_FOLDER = join(MULTIVERSE_FOLDER, 'multiverse', 'boba_logs')
    SUM_DF_PATH = join(MULTIVERSE_FOLDER, 'multiverse', 'summary.csv')
    
    
    df = pd.read_csv(SUM_DF_PATH)
    min_decs = get_min_decisions(df)
    print(f'{bcolors.OKCYAN}====== Sampled Universes to Run ======')
    pprint(min_decs)
    debug_multiverse = DebugMultiverse(LOG_FOLDER, df)
    debug_multiverse.print_common_decisions(768)
    debug_multiverse.print_common_output(768, 532)
    debug_multiverse.print_decision_and_code(2)
    print('here')