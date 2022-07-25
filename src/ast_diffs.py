import ast
from dataclasses import dataclass, field
from collections import defaultdict 
import datetime
import copy
import os.path as osp
import re
from typing import Union, List, Dict, Tuple
from itertools import zip_longest


from src.ast_traverse import NodeVisitorStack
from src.boba.parser import Parser
from src.our_ydiff import OurHunk, OurUnifiedDiff

@dataclass
class CodeInfo:
    code: str = ""
    lineno: int = -1
    endlineno: int = -1
    col_offset: int = -1
    end_col_offset: int = -1
    
    
@dataclass
class CodeCompare:
    orig_code_info: CodeInfo
    new_code_info: CodeInfo

def ast_parse_subnode(code_str):
    return ast.parse(code_str).body[0].value

def parse_constant_for_boba_var_node(node):
    if not isinstance(node, ast.Constant):
        return None
    s = str(node.value)
    # https://stackoverflow.com/questions/35930203/regex-get-anything-between-double-curly-braces
    regexp = re.compile('(?<=\{\{)[a-zA-Z0-9._]*?(?=\}\})')
    match = regexp.search(s)
    # matches exactly one boba variable
    if match and len(match.regs) == 1 and (match.regs[0][0] == 2 and match.regs[0][1] == (match.endpos - 2)): 
        return match.group()
    return None
        
    
def compare_ast(node1: Union[ast.expr, List[ast.expr]], node2: Union[ast.expr, List[ast.expr]]) -> bool:
    if type(node1) is not type(node2):
        return False

    if isinstance(node1, ast.AST):
        for k, v in vars(node1).items():
            if k in {"lineno", "end_lineno", "col_offset", "end_col_offset", "ctx"}:
                continue
            if not compare_ast(v, getattr(node2, k)):
                return False
        return True

    elif isinstance(node1, list) and isinstance(node2, list):
        return all([compare_ast(n1, n2) for n1, n2 in zip_longest(node1, node2)])
    else:
        return node1 == node2



class ASTDiff:
    def __init__(self, fpath, boba_parser: Parser):
        self.boba_parser = boba_parser
        self.changes = []
        self.no_changes = []
        self.universe_num = int(osp.basename(fpath).split('.')[0].split('_')[-1])
        with open(fpath, 'r') as f:
            self.changed_code = f.read()
        self.fpath = fpath
        self.no_changes: Dict[Tuple[str, int], List[CodeInfo]] = None
        self.changes: Dict[Tuple[str, int], List[CodeCompare]] = None
        self.changes, self.no_changes = self._get_ast_diff_changes()
        self.new_spec, self.meta_str = self._get_ast_diffs_to_boba_json_change()
        
        
    def _get_ast_diff_changes(self):
        changed_code_history = self.boba_parser.history[self.universe_num - 1]
        path_ind = changed_code_history.path
        changed_code_ast = ast.parse(self.changed_code)
        orig_code_template_ast = self.boba_parser.paths_ast[path_ind]
        
        nv_changed = NodeVisitorStack()
        nv_template = NodeVisitorStack()
        
        nv_changed.stack.append(changed_code_ast)
        nv_template.stack.append(orig_code_template_ast)
        
        changes = defaultdict(list)
        no_changes = defaultdict(list)
        
        while len(nv_changed.stack) > 0 and len(nv_template.stack) > 0: #does not detect Constant node changes
            n1 = nv_changed.pop_stack()
            n2 = nv_template.pop_stack()
            if n1.__class__ == n2.__class__ and isinstance(n1, ast.AST):
                nv_changed.add_children_to_stack(n1)
                nv_template.add_children_to_stack(n2)
            else:
                boba_var = parse_constant_for_boba_var_node(n2)
                if boba_var is not None and boba_var in changed_code_history.decision_dict:
                    orig_code_str, option_idx = changed_code_history.decision_dict[boba_var]
                    if not compare_ast(n1, ast_parse_subnode(orig_code_str)):
                        changed_code_str = ast.unparse(n1)  #  The produced code string will not necessarily be equal to the original code that generated the ast.AST object
                        orig_code_info = CodeInfo(code=orig_code_str,
                                                lineno=n2.lineno)
                        new_code_info = CodeInfo(code=changed_code_str,
                                                lineno=n1.lineno,
                                                endlineno=n1.end_lineno,
                                                col_offset=n1.col_offset,
                                                end_col_offset=n1.end_col_offset)
                        
                        change = CodeCompare(orig_code_info, new_code_info)
                        changes[(boba_var, option_idx)].append(change)
                    else:
                        code_info = CodeInfo(code=orig_code_str,
                                            lineno=n1.lineno,
                                            endlineno=n1.end_lineno,
                                            col_offset=n1.col_offset,
                                            end_col_offset=n1.end_col_offset)
                        no_changes[(boba_var, option_idx)].append(code_info)
                else:
                    pass
                    # nv_changed.add_children_to_stack(n1)
                    # nv_template.add_children_to_stack(n2)
        return changes, no_changes      
    
    
    def _get_ast_diffs_to_boba_json_change(self):
        code_parser = self.boba_parser.code_parser
        new_spec = copy.deepcopy(code_parser.spec)
        decisions = new_spec['decisions']
        
        meta_strs = []
        for (boba_var, option_idx), code_cmp in self.changes.items():
            decision_dict = decisions[code_parser.boba_var_to_decision_ind[boba_var]]
            decision_dict['options'][option_idx] = code_cmp[0].new_code_info.code
            
            if (boba_var, option_idx) in self.no_changes:
                meta_str = f'Warning: not all instantiations of {boba_var} option {option_idx} changed to {code_cmp[0].new_code_info.code}:\n'
                for i, code_info in enumerate(self.no_changes[(boba_var, option_idx)]):
                    meta_str += f'\t{i+1}. In line {code_info.lineno} still {code_info.code}\n'
                meta_strs.append(meta_str)
                
        
        return new_spec, '\n'.join(meta_strs)
    
    
    def get_ast_boba_json_diff(self):
        spec_hunk = OurHunk.init_from_boba_json(self.boba_parser.code_parser.spec, self.new_spec, meta=self.meta_str)
        old_path = f'--- Boba Template {self.boba_parser.fn_script} {datetime.datetime.fromtimestamp(osp.getmtime(self.boba_parser.fn_script))}\n'
        new_path = f'+++ Updated Boba Template After Universe {self.fpath} {datetime.datetime.fromtimestamp(osp.getmtime(self.fpath))}\n'
        diff = OurUnifiedDiff([], old_path, new_path, [spec_hunk])
        return diff
  
    
