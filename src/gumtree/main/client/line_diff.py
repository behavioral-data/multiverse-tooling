from collections import defaultdict
from dataclasses import dataclass
import difflib
from typing import Dict, List, Tuple
from src.gumtree.main.client.client import Client

from src.boba.parser import Parser
from src.gumtree.main.trees.tree import Tree
from ydiff import Hunk
import ydiff
from src.our_ydiff import OurUnifiedDiff, UnmatchedLineDiffMarker


@dataclass(frozen=True, eq=True)
class Pos:
    lineno: int = -1
    col_offset: int = -1
    end_lineno: int = -1
    end_col_offset: int = -1
    
        
    def get_code(self, code: str):
        if self.lineno == -1:
            return ""
        code_lines = code.encode(encoding = 'UTF-8', errors = 'strict')
        code_lines = code.split('\n')
        code_lines = code_lines[self.lineno - 1 : self.end_lineno]
        if len(code_lines) == 1:
            return code_lines[0][self.col_offset: self.end_col_offset]
        else:
            code_lines[0] = code_lines[0][self.col_offset:]
            code_lines[-1] = code_lines[-1][:self.end_col_offset]
            return "\n".join(code_lines)
        
@dataclass
class LinePosMark:
    start_col: int
    end_col: int
    mark: str

class ProcessedHunk(Hunk):
    def __init__(self, 
                 hunk_headers: List[str], 
                 hunk_meta: str, 
                 old_text_lines: List[Tuple[str, bool]], 
                 new_text_lines: List[Tuple[str, bool]],
                 old_text_str: str,
                 new_text_str: str):
        old_addr = (1, len(old_text_lines))
        new_addr = (1, len(new_text_lines))
        super().__init__(hunk_headers, hunk_meta, old_addr, new_addr)
        self.old_text_lines = old_text_lines
        self.new_text_lines = new_text_lines
        self.old_text_str = old_text_str
        self.new_text_str = new_text_str 
        self.mdiff_list = self.calc_mdiff()
        
    def calc_mdiff(self) -> List:
        res = []
        old_ind = 0
        new_ind = 0
        for old, new, _ in difflib._mdiff(self.old_text_str.split('\n'), self.new_text_str.split('\n')):
            old_changed = self.old_text_lines[old_ind][1]
            new_changed = self.new_text_lines[new_ind][1]
            if old[0]:
                from_line_tup = (old_ind + 1, self.old_text_lines[old_ind][0])
                old_ind += 1
            else:
                from_line_tup = (None, '')
            
            if new[0]:
                to_line_tup = (new_ind + 1, self.new_text_lines[new_ind][0])
                new_ind += 1
            else:
                to_line_tup = (None, '')
            res.append((from_line_tup, to_line_tup, old_changed, new_changed))
        return res
    
    def mdiff(self):
        return iter(self.mdiff_list)
        
class LineDiff(Client):
    INSERT_TAG = '\x00+'
    DEL_TAG = '\x00-'
    UPDATE_TAG = '\x00^'
    RESET_TAG = '\x01'
    
    def __init__(self, ps: Parser, universe_code, universe_num):
        self.boba_parser = ps
        self.universe_num = universe_num
        template_code = self.boba_parser.paths_code[ps.history[universe_num - 1].path]
        self.default_configurations = {
            "generator": ("boba_python_template", "python"),
            "matcher": "boba",
            "parser_history": ps.history[universe_num - 1],
            "priority_queue": "python"
        }
    
        super().__init__(template_code, universe_code, self.default_configurations)
        self.diff = self.get_diff()
        self.classifier = self.diff.createRootNodesClassifier()
        self.src_code_lines = self.src_code.split('\n')
        self.dst_code_lines = self.dst_code.split('\n')
    
    def run(self):
        self.produce()

    def produce(self):
        c = self.classifier 
        src_line_to_mark: Dict[int, List[LinePosMark]] = defaultdict(list)
        dst_line_to_mark: Dict[int, List[LinePosMark]] = defaultdict(list)
        
        for t in self.diff.src.root.pre_order():
            pos = Pos(t.metadata.get("lineno", -1),
                          t.metadata.get("col_offset", -1),
                          t.metadata.get("end_lineno", -1),
                          t.metadata.get("end_col_offset", -1)
                )
            if t in c.get_updated_srcs():
                self.add_line_mark(pos, self.src_code_lines, src_line_to_mark, self.UPDATE_TAG)
            if t in c.get_deleted_srcs():
                self.add_line_mark(pos, self.src_code_lines, src_line_to_mark, self.DEL_TAG)
                
        for t in self.diff.dst.root.pre_order():
            pos = Pos(t.metadata.get("lineno", -1),
                          t.metadata.get("col_offset", -1),
                          t.metadata.get("end_lineno", -1),
                          t.metadata.get("end_col_offset", -1)
                )
            if t in c.get_updated_dsts():
                self.add_line_mark(pos, self.dst_code_lines, dst_line_to_mark, self.UPDATE_TAG)
            if t in c.get_inserted_dsts():
                self.add_line_mark(pos, self.dst_code_lines, dst_line_to_mark, self.INSERT_TAG)
        
        src_marks = self.process_line_marks_to_mark_list(src_line_to_mark)
        dst_marks = self.process_line_marks_to_mark_list(dst_line_to_mark)
        src_str_lines = self.insert_mark_list_code_str(src_marks, self.src_code_lines)
        dst_str_lines = self.insert_mark_list_code_str(dst_marks, self.dst_code_lines)
        
        hunk = ProcessedHunk([], 'Metadata\n', src_str_lines, dst_str_lines, self.src_code, self.dst_code)
        diff = OurUnifiedDiff([], '--- Boba Template\n', f'+++ Universe {self.universe_num} Spec\n', [hunk])
        marker = UnmatchedLineDiffMarker(side_by_side=True, width=80,  wrap=True)
        color_diff = marker.markup(diff)
        for line in color_diff:
            a = line.encode('utf-8')
            print(a.decode(), end='')
                
    
    @staticmethod
    def add_line_mark(pos: Pos, 
                      code_lines: List[str], 
                      line_to_mark: Dict[int, List[LinePosMark]],
                      mark: str):
        for lineno in range(pos.lineno, pos.end_lineno + 1):
            if lineno == pos.lineno:
                start_col = pos.col_offset
            else:
                start_col = 0
            if lineno == pos.end_lineno:
                end_col = pos.end_col_offset
            else:
                end_col = len(code_lines[lineno-1])
            line_to_mark[lineno].append(LinePosMark(start_col, end_col, mark))
    
    @staticmethod  
    def process_line_marks_to_mark_list(line_to_mark: Dict[int, List[LinePosMark]]) -> Dict[int, List[Tuple[int, str]]]:
        """
        The tuple in the list of tuples contain (line_col, mark_to_insert)
        """
        marks = {}
        for line, line_pos_marks in line_to_mark.items():
            line_pos_queue = sorted(line_pos_marks, key=lambda pos_mark: (pos_mark.start_col, -pos_mark.end_col))
            ind = 1
            marks_stack = [line_pos_queue[0]]
            marks_pos = [(line_pos_queue[0].start_col, line_pos_queue[0].mark)]
            
            def clear_stack(marks_stack, marks_pos):
                previous_mark = marks_stack.pop()
                marks_pos.append((previous_mark.end_col, LineDiff.RESET_TAG))
                if marks_stack:
                    marks_pos.append((previous_mark.end_col, marks_stack[-1].mark))
                    
            
            while ind < len(line_pos_queue):
                line_pos_mark = line_pos_queue[ind]
                if line_pos_mark.start_col > marks_stack[-1].end_col:
                    while marks_stack and line_pos_mark.start_col > marks_stack[-1].end_col: # non-overlapping
                        clear_stack(marks_stack, marks_pos)
                    marks_pos.append((line_pos_mark.start_col, LineDiff.RESET_TAG))
                    marks_pos.append((line_pos_mark.start_col, line_pos_mark.mark))
                else: #overlapping
                    marks_pos.append((line_pos_mark.start_col, LineDiff.RESET_TAG))
                    marks_pos.append((line_pos_mark.start_col, line_pos_mark.mark))
                marks_stack.append(line_pos_mark)
                ind += 1

            while marks_stack:
                clear_stack(marks_stack, marks_pos)    
            marks[line] = marks_pos
        return marks

    @staticmethod
    def insert_mark_list_code_str(marks: Dict[int, List[Tuple[int, str]]], 
                                  code_lines: List[str]) -> List[Tuple[str, bool]]:
        ret = []
        for i, code_line in enumerate(code_lines):
            lineno = i + 1
            if lineno in marks:
                acc = 0
                char_str = list(code_line)
                for pos, mark in marks[lineno]:
                    char_str.insert(pos + acc, mark)
                    acc += 1
                ret.append((''.join(char_str), True))
            else:
                ret.append((code_line, False))
        return ret
    
    def get_dst_code_from_src(self, src):
        t = self.diff.mappings.get_dst_for_src(src)
        pos = Pos(t.metadata.get("lineno", -1),
                  t.metadata.get("col_offset", -1),
                  t.metadata.get("end_lineno", -1),
                  t.metadata.get("end_col_offset", -1)
        )
        return pos
    
    def get_src_code_from_dst(self, dst):
        t = self.diff.mappings.get_src_for_dst(dst)
        pos = Pos(t.metadata.get("lineno", -1),
                  t.metadata.get("col_offset", -1),
                  t.metadata.get("end_lineno", -1),
                  t.metadata.get("end_col_offset", -1)
        )
        return pos

    
if __name__ == "__main__":
    from src.utils import load_parser_example
    
    from src.utils import load_parser_example, read_universe_file, VIZ_DIR, DATA_DIR
    import os.path as osp
    from src.utils import save_viz_code_pdf
    from src.gumtree.main.client.dot_diff import DotDiff
    dataset, ext = 'fertility', 'py'
    save_file = osp.join(DATA_DIR, f'{dataset}_template_parser_obj_0718.pickle')
    ps = load_parser_example(dataset, ext, save_file)
    universe_num = 3
    universe_code = read_universe_file(universe_num, dataset, ext)
    line_diff = LineDiff(ps, universe_code, universe_num)
    res = line_diff.run()