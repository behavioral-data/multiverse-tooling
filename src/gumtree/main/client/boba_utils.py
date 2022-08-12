

from collections import defaultdict
from copy import deepcopy
from typing import Dict, List, Tuple, Union
from src.gumtree.main.trees.tree import Tree

from src.boba.codeparser import Block, BlockCode
from src.gumtree.main.gen.python_tree_generator import PythonParsoTreeGenerator, PythonTreeGenerator

from src.gumtree.main.trees.tree_chunk import MappedBobaVar

def get_universe_blocks_from_template_blocks(template_blocks: Dict[str, Block], 
                                             universe_blocks: List[BlockCode]) -> Block:
    blocks = []
    for k, v in template_blocks.items():
        if any((k == str(k1)) for k1 in universe_blocks):
            blocks.append(v)
    return blocks

def chunk_code_from_pos(code: str, mappings: List[Tuple[str, Union[Tree, MappedBobaVar]]]):
    prev_end_pos = 0
    chunks = []
    updated_pos = []
    cur_new_pos = 0
    mappings.sort(key=lambda x: x[1].pos)
    for s, t in mappings:
        chunks.append(code[prev_end_pos: t.pos])
        cur_new_pos += (t.pos - prev_end_pos)
        chunks.append(s)
        updated_pos.append((s, (cur_new_pos, cur_new_pos + len(s))))
        cur_new_pos += len(s)
        prev_end_pos = t.end_pos
    chunks.append(code[prev_end_pos:])
    return ''.join(chunks), updated_pos

def chunk_code_from_line_and_col(code: str, mappings: List[Tuple[str, Union[Tree, MappedBobaVar]]]):
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
        new_block = deepcopy(blk)
        blk_dec_name = blk.dec_name.split(':')[0]
        if str(blk) in count_block:
            new_name = blk_dec_name + f'_{count_block[str(blk)]}'
            if blk.dec_name == blk.opt_name:
                new_block.opt_name = new_name
            new_block.dec_name = new_name

        else:
            count_block[str(blk)] += 1
            new_block.dec_name = blk_dec_name
        ret.append(new_block)
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
    

def get_tree(src_code, gen_name='python_parso'):
    if gen_name == 'python_parso':
        generator = PythonParsoTreeGenerator()
    elif gen_name == 'python':
        generator = PythonTreeGenerator()
    else:
        raise ValueError(f'Unsupported gen_name {gen_name}')
    tree = generator.generate_tree(src_code).root
    return tree