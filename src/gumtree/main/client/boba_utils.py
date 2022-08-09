

from collections import defaultdict
from typing import Dict, List, Tuple
from src.gumtree.main.trees.tree import Tree

from src.boba.codeparser import BlockCode
from src.gumtree.main.gen.boba_tree_generator import BobaPythonTemplateTreeGeneator, BobaRTemplateGenerator
from src.gumtree.main.gen.python_tree_generator import PythonTreeGenerator


def chunk_code(code: str, mappings: List[Tuple[str, Tree]]):
    """
    Replaces strings in code that are specified by AST Tree.
    For each s, t in mappings. We replace the code specified by t with
    the string s.
    """
    prev_line = 1
    prev_end_col = 0
    chunks = []
    code_lines = code.split('\n')
    mappings.sort(key=lambda x: x[1].metadata['lineno'])
    for s, t in mappings:
        mapped_lineno = t.metadata['lineno']
        mapped_col_offset  = t.metadata['col_offset']
        new_chunk = []
        if prev_line == mapped_lineno:
            new_chunk.append(code_lines[prev_line-1][prev_end_col:mapped_col_offset])
        else:
            new_chunk.append(code_lines[prev_line-1][prev_end_col:] + '\n')
            mid_lines = code_lines[prev_line: mapped_lineno]
            mid_lines[-1] = mid_lines[-1][:mapped_col_offset]
            new_chunk.append('\n'.join(mid_lines))
        chunks.append(''.join(new_chunk))    
        
        prev_line = t.metadata['end_lineno']
        prev_end_col = t.metadata['end_col_offset']
        chunks.append(s)

    new_chunk = []
    if prev_line == len(code_lines):
        new_chunk.append(code_lines[prev_line-1][prev_end_col:])
    else:
        new_chunk.append(code_lines[prev_line-1][prev_end_col:] + '\n')
        mid_lines = code_lines[prev_line: len(code_lines)]
        new_chunk.append('\n'.join(mid_lines))
    chunks.append(''.join(new_chunk))
    return ''.join(chunks)


def clean_code_blocks(code_blocks: List[BlockCode]):
    count_block = defaultdict(int)
    ret = []
    for blk in code_blocks:
        blk_dec_name = blk.dec_name.split(':')[0]
        if str(blk) in count_block:
            new_name = blk_dec_name + f'_{count_block[str(blk)]}'
            if blk.dec_name == blk.opt_name:
                blk.opt_name = new_name
            blk.dec_name = new_name

        else:
            count_block[str(blk)] += 1
            blk.dec_name = blk_dec_name
        ret.append(blk)
    return ret

def parse_boba_var_config_ast(boba_config_t: Tree) -> Dict[str, List[Tree]]:
    boba_var_trees = []
    for t in boba_config_t.pre_order():
        # t.parent will be of the form '"var": "fertility_bounds", "options": [\n\t  [[7, 14], [17, 25], [17, 25]],\n\t  [[6, 14], [17, 27], [17, 27]],\n\t  [[9, 17], [18, 25], [18, 25]],\n\t  [[8, 14], [1, 7], [15, 28]],\n\t  [[9, 17], [1, 8], [18, 28]]\n\t]'
        if t.label == '"options"' and t.parent.node_type == 'dictorsetmaker' and len(t.parent.children) == 5:
            boba_var_trees.append(t.parent)
    var_to_options: Dict[str, List[Tree]] = {}
    for t in boba_var_trees:
        label, options = parse_boba_var_tree(t)
        var_to_options[label] = options
    return var_to_options
    
def parse_boba_var_tree(t: Tree) -> Tuple[str, List[Tree]]:
    """
    Example t
    [PythonTree: string ("var") [120, 125] ,
        PythonTree: string ("fertility_bounds") [127, 145] ,
        PythonTree: operator (,) [145, 146] ,
        PythonTree: string ("options") [147, 156] ,
        PythonTree: atom [158, 327]]
    """
    boba_var_t = t.children[1]
    option_list_t = t.get_child_from_url('4.0') # get the node corresponding to the options
    options_t = [option_list_t.children[i]for i in range(0, len(option_list_t.children), 2)]
    return eval(boba_var_t.label), options_t
    

def get_tree(src_code, gen_name='python'):
    if gen_name == 'python':
        generator = PythonTreeGenerator()
    elif gen_name == "boba_python":
        generator = BobaPythonTemplateTreeGeneator()
    elif gen_name == "boba_r":
        generator = BobaRTemplateGenerator()
    else:
        raise ValueError(f'Unsupported gen_name {gen_name}')
    tree = generator.generate_tree(src_code).root
    return tree