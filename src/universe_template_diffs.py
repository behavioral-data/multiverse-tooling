import bisect
from codecs import Codec
import datetime
import difflib
import os.path as osp
import ydiff

from src.boba.parser import Parser
from src.our_ydiff import OurHunk, OurUnifiedDiff
from src.ast_diffs import ASTDiff


def read_file_against_template(fpath, code_blocks):
    orig_code = ''.join([b.code_str for b in code_blocks])
    with open(fpath, 'r') as f:
        changed_code = f.read()
    orig_code_lines = orig_code.split('\n')
    changed_code_lines = changed_code.split('\n')
    return orig_code_lines, changed_code_lines

def get_diff(fpath: str, boba_parser: Parser):
    universe_num = int(osp.basename(fpath).split('.')[0].split('_')[-1])
    code_blocks = boba_parser.blocks_code[universe_num-1]
    orig_code_lines, changed_code_lines = read_file_against_template(fpath, code_blocks)
    
    def cumsum(code_blocks):
        r, s = [], 0
        for code_block in code_blocks:
            l = code_block.code_num_lines
            r.append(l + s)
            s += l
        return r
    cum_sum = cumsum(code_blocks)
    
    hunks = []
    for group in difflib.SequenceMatcher(None,orig_code_lines, changed_code_lines).get_grouped_opcodes(n=3):
        first, last = group[0], group[-1]
        
        orig_start_line, orig_end_line = first[1], last[2]
        change_start_line, change_end_line = first[3], last[4]
        
        blocks = []
        for tag, i, i2, j, j2 in group:
            if tag in {'replace', 'delete', 'insert'}:
                start_block = code_blocks[bisect.bisect_left(cum_sum, i)]
                end_block = code_blocks[bisect.bisect_left(cum_sum, i2)]
                blocks.append((str(start_block), str(end_block)))
            
        block_names = set([name for b in blocks for name in b ])
                
        hunk = OurHunk.init_from_block_names(block_names,
                                             old_addr=(orig_start_line, orig_end_line),
                                             new_addr=(change_start_line, change_end_line),
                                             old_text='\n'.join(orig_code_lines[orig_start_line: orig_end_line]),
                                             new_text='\n'.join(changed_code_lines[change_start_line: change_end_line])
                                             )
        hunks.append(hunk)

    old_path = f'--- Boba Template {boba_parser.fn_script} {datetime.datetime.fromtimestamp(osp.getmtime(boba_parser.fn_script))}\n'
    new_path = f'+++ Universe Spec {fpath} {datetime.datetime.fromtimestamp(osp.getmtime(fpath))}\n'
    
    diff = OurUnifiedDiff([], old_path, new_path, hunks)
    
    return diff

def print_diff(diff: OurUnifiedDiff):
    marker = ydiff.DiffMarker(side_by_side=True, width=80,  wrap=True)
    color_diff = marker.markup(diff)
    for line in color_diff:
        a = line.encode('utf-8')
        print(a.decode(), end='')
            

if __name__ == '__main__':
    import os.path as osp
    from src.utils import DATA_DIR
    import pickle 
    
    DATASET = 'fertility'
    EXT = 'py'
    script = osp.join(DATA_DIR, DATASET, f'template.{EXT}')
    out = osp.join(DATA_DIR, DATASET)
    
    save_file = osp.join(DATA_DIR, f'{DATASET}_template_parser_obj_0718.pickle')
    
    if not osp.exists(save_file):
        ps = Parser(script, out, None)
        ps.main()
    
        with open(save_file, 'wb') as f:
            pickle.dump(ps, f)
    with open(save_file, 'rb') as f:
        ps = pickle.load(f)
    universe_code_dir = osp.join(DATA_DIR, DATASET, 'multiverse', 'code')
    universe_num = 3
    universe_path = osp.join(universe_code_dir, f'universe_{universe_num}.{EXT}')
    if EXT == 'py':
        ast_diff = ASTDiff(universe_path, ps)
        diff = ast_diff.get_ast_boba_json_diff()
        print_diff(diff)
    print_diff(get_diff(universe_path, ps))
    
    # universe_num = 5
    # universe_path = osp.join(universe_code_dir, f'universe_{universe_num}.{EXT}')
    # print_diff(get_diff(universe_path, ps))
    
    # universe_num = 7
    # universe_path = osp.join(universe_code_dir, f'universe_{universe_num}.{EXT}')
    # print_diff(get_diff(universe_path, ps))
    
    

        
    