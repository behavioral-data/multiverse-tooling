from typing import List
from src.boba.parser import Parser

import os.path as osp
from src.gumtree.main.client.boba_template_diff import TemplateDiff
from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.client.template_builder import CodePos

from src.gumtree.main.trees.tree_chunk import MappedBobaVar, OffsetsFromBobaVar


class TemplateDiffView:
    def __init__(self, ps: Parser, dst_file: str):
        universe_num = int(osp.basename(dst_file).split('.')[0].split('_')[-1])
        self.dst_file = dst_file
        with open(dst_file, 'r') as f:
            universe_code = f.read()
        self.template_diff: TemplateDiff = TemplateDiff(ps, universe_code, universe_num)
        self.template_code_pos = self.template_diff.template_code_pos
        self.new_template_u_code_pos: CodePos = self.template_diff.new_template_u_code_pos
        self.new_template_i_code_pos: CodePos = self.template_diff.new_template_i_code_pos
        
    def get_all_config(self):
        return ('config = {{ file: "{}", newUniverse: {}, '
                'oldTemplate: {}, newTemplate: {}, '
                'templateMappings: {}, newUniTemplateMappings: {}, '
                'editor: {}}};'.format('test.py', 
                                       self.get_new_universe_js_config(),
                                       self.get_old_template_js_config(),
                                       self.get_new_template_js_config(),
                                       self.get_templates_mapped_js_config(),
                                       self.get_new_universe_new_template_mapped_js_config(),
                                       '{url: "/editor"}'))
    
    def get_boba_var_choice_tree_from_child(self, t: Tree):
        cand_node = t.parent.parent.parent
        path = []
        while not(cand_node.node_type == 'dictorsetmaker' 
                  and len(cand_node.children) == 5 
                  and cand_node.children[3].label == '"options"'):
            parent = t.parent
            path.append(str(parent.get_child_position(t)))
            t = parent
            cand_node = t.parent.parent.parent
        return t, '.'.join(reversed(path))
    
    def get_new_universe_mapped_boba_nodes_from_spec_tree(self, t: Tree) -> List[MappedBobaVar]:
        new_choice_spec_tree, child_url = self.get_boba_var_choice_tree_from_child(t)
        pos_in_parent = new_choice_spec_tree.position_in_parent()
        old_choice_spec_tree = self.template_diff.spec_diff.mappings.get_src_for_dst(new_choice_spec_tree.parent).children[pos_in_parent]
        boba_var = self.template_diff.template_spec_tree_to_boba_choice_var[old_choice_spec_tree]
        ret = [] 
        for mbv in self.template_diff.mapped_boba_vars:
            if mbv.boba_var == boba_var and mbv.boba_opt_str != '':
                ret.append(mbv) 
        return ret
    
    def get_new_universe_js_config(self):
        c = self.template_diff.classifier
        c_spec = self.template_diff.spec_classifier

        b: List[str] = []
        b.append("{")
        b.append("url:")
        b.append('"/new_universe",')
        b.append("ranges: [")

        for t in self.template_diff.diff.dst.root.pre_order():
            if t in c.get_moved_dsts():
                self.append_range(b, t, kind="moved")
            if t in c.get_updated_dsts():
                self.append_range(b, t, kind="updated")
            if t in c.get_inserted_dsts():
                self.append_range(b, t, kind="inserted")
        b.append("],")
        b.append("}")
        return " ".join(b)
    
    def get_new_template_js_config(self):
        c = self.template_diff.classifier
        c_spec = self.template_diff.spec_classifier
        b: List[str] = []
        b.append("{")
        b.append("url:")
        b.append('"/new_template",')
        b.append("ranges: [")
        for t in self.template_diff.spec_diff.dst.root.pre_order():
            boba_conf_offset = self.new_template_u_code_pos.get_boba_config_pos_offset()
            if t in c_spec.get_moved_dsts():
                self.append_range(b, t, kind="moved", offset=boba_conf_offset)
            if t in c_spec.get_updated_dsts():
                self.append_range(b, t, kind="updated", offset=boba_conf_offset)
            if t in c_spec.get_inserted_dsts():
                self.append_range(b, t, kind="inserted", offset=boba_conf_offset)

        for t in self.template_diff.diff.dst.root.pre_order(): # if some are not mapped to boba nodes then it will be longer
            offsets = self.get_offset(t, self.new_template_u_code_pos, self.template_diff.new_u_t_diff)
            if offsets is not None:
                if t in c.get_moved_dsts():
                    self.append_range(b, t, kind="moved",  offset=offsets[0], offset_end=offsets[1])
                if t in c.get_updated_dsts():
                    self.append_range(b, t, kind="updated",  offset=offsets[0], offset_end=offsets[1])
                if t in c.get_inserted_dsts():
                    self.append_range(b, t, kind="inserted", offset=offsets[0], offset_end=offsets[1])
        
        for s, (new_i_pos, new_i_end_pos) in self.template_diff.new_boba_var_pos:
            new_t_pos = self.new_template_i_code_pos.get_pos_offset_from_pos(new_i_pos) + new_i_pos
            new_t_end_pos = self.new_template_i_code_pos.get_pos_offset_from_pos(new_i_end_pos) + new_i_end_pos
            b.append("{")
            b.append(f"from: {new_t_pos},")
            b.append(f"to: {new_t_end_pos},")
            b.append(f"index: 2147483647,")
            b.append(f'kind: "boba-var",')
            b.append(f'tooltip: "",')
            b.append("},")
            
                    
        
        b.append("],")
        b.append("}")
        return " ".join(b)
    
    def get_offset(self, 
                   t: Tree,
                   blk_code_pos: CodePos, 
                   boba_var_offset: OffsetsFromBobaVar):
        boba_var_offset_pos_end = boba_var_offset.get_offset(t.end_pos)
        boba_var_offset_pos_start = boba_var_offset.get_offset(t.pos)
        if boba_var_offset_pos_end is None or boba_var_offset_pos_start is None:
            return None
        offset_from_blks = blk_code_pos.get_pos_offset(t)
        starting_line_pos = blk_code_pos.get_u_block_starting_line_pos(t)
        boba_var_offset_pos_from_blks = boba_var_offset.get_offset(starting_line_pos)
        offset_start = offset_from_blks - (boba_var_offset_pos_start - boba_var_offset_pos_from_blks)
        offset_end = offset_from_blks - (boba_var_offset_pos_end - boba_var_offset_pos_from_blks)
        return offset_start, offset_end
    
    def get_old_template_js_config(self):
        c = self.template_diff.classifier
        c_spec = self.template_diff.spec_classifier
        b: List[str] = []
        b.append("{")
        b.append("url:")
        b.append('"/old_template",')
        b.append("ranges: [")
        for t in self.template_diff.spec_diff.src.root.pre_order():
            boba_conf_offset = self.template_code_pos.get_boba_config_pos_offset()
            if t in c_spec.get_moved_srcs():
                self.append_range(b, t, kind="moved", offset=boba_conf_offset)
            if t in c_spec.get_updated_srcs():
                self.append_range(b, t, kind="updated", offset=boba_conf_offset)
            if t in c_spec.get_deleted_srcs():
                self.append_range(b, t, kind="deleted", offset=boba_conf_offset)

        
        for t in self.template_diff.diff.src.root.pre_order():
            offsets = self.get_offset(t, self.template_code_pos, self.template_diff.old_u_t_diff)
            if offsets is not None:
                if t in c.get_moved_srcs():
                    self.append_range(b, t, kind="moved", offset=offsets[0], offset_end=offsets[1])
                if t in c.get_updated_srcs():
                    self.append_range(b, t, kind="updated", offset=offsets[0], offset_end=offsets[1])
                if t in c.get_deleted_srcs():
                    self.append_range(b, t, kind="deleted", offset=offsets[0], offset_end=offsets[1])
        b.append("],")
        b.append("}")
        return " ".join(b)
    
    def get_templates_mapped_js_config(self):
        c = self.template_diff.classifier
        c_spec = self.template_diff.spec_classifier
        b = ["["]
        for t in self.template_diff.spec_diff.src.root.pre_order():
            if t in c_spec.get_moved_srcs() or t in c_spec.get_updated_srcs():
                d = self.template_diff.spec_diff.mappings.get_dst_for_src(t)
                offset_template = self.template_code_pos.get_boba_config_pos_offset()
                offset_new_template = self.new_template_u_code_pos.get_boba_config_pos_offset()
                b.append("[{}, {}, {}, {}],".format(t.pos + offset_template,
                                                   t.end_pos + offset_template,
                                                   d.pos + offset_new_template,
                                                   d.end_pos + offset_new_template))
        for t in self.template_diff.diff.src.root.pre_order():
            if t in c.get_moved_srcs() or t in c.get_updated_srcs():
                d = self.template_diff.diff.mappings.get_dst_for_src(t)
                offset_templates = self.get_offset(t, self.template_code_pos, self.template_diff.old_u_t_diff)
                offset_new_templates = self.get_offset(d, self.new_template_u_code_pos, self.template_diff.new_u_t_diff)
                if offset_templates is not None and offset_new_templates is not None:
                    b.append("[{}, {}, {}, {}],".format(t.pos + offset_templates[0],
                                                    t.end_pos + offset_templates[1],
                                                    d.pos + offset_new_templates[0],
                                                    d.end_pos + offset_new_templates[1]))
                
        b.append("]")
        return " ".join(b)
    
    def get_new_universe_new_template_mapped_js_config(self):
        c = self.template_diff.classifier
        c_spec = self.template_diff.spec_classifier
        b = ["["]
        for t in self.template_diff.spec_diff.dst.root.pre_order():
            if c_spec.changed_dst_tree(t):
                mapped_boba_vars = self.get_new_universe_mapped_boba_nodes_from_spec_tree(t)
                for mbv in mapped_boba_vars:
                    b.append("[{}, {}, {}, {}],".format(mbv.pos,
                                                        mbv.end_pos,
                                                        t.pos,
                                                        t.end_pos))
                        
        for t in self.template_diff.diff.dst.root.pre_order():
            if t in c.get_moved_dsts() or t in c.get_inserted_dsts() or t in c.get_updated_dsts():
                offsets = self.get_offset(t, self.new_template_u_code_pos, self.template_diff.new_u_t_diff)
                if offsets is not None:
                    b.append("[{}, {}, {}, {}],".format(t.pos,
                                                        t.end_pos,
                                                        t.pos + offsets[0],
                                                        t.end_pos + offsets[1]))
        b.append("]")
        return " ".join(b)
                
            
    def append_range(self, b: List[str], t: Tree, kind: str, offset: int=None, offset_end: int=None):
        if offset is None:
            offset = 0
        if offset_end is None:
            offset_end = offset
        b.append("{")
        b.append(f"from: {t.pos + offset},")
        b.append(f"to: {t.end_pos + offset_end},")
        b.append(f"index: {t.tree_metrics.depth if t.node_type != 'BobaVar' else 1000000},")
        b.append(f'kind: "{kind}",')
        b.append(f'tooltip: "{self.tooltip(t)}",')
        b.append("},")
    

    def tooltip(self, t: Tree):
        if t.parent is None:
            return t.node_type.replace('\n', '')
        else:
            s =  t.parent.node_type + "/" + t.node_type
            return s.replace('\n', '')
        
if __name__ == "__main__":
    from src.utils import load_parser_example, DATA_DIR
    import os.path as osp
    import pickle
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
    
    # tdv = main_helper('/projects/bdata/kenqgu/Research/MultiverseProject/MultiverseTooling/multiverse-tooling/data/hurricane/multiverse/code/universe_3.R')
    tdv = main_helper('/projects/bdata/kenqgu/Research/MultiverseProject/MultiverseTooling/multiverse-tooling/data/fertility/multiverse/code/universe_3.py')
    # tdv = main_helper('/projects/bdata/kenqgu/Research/MultiverseProject/MultiverseTooling/multiverse-tooling/data/playing_around/multiverse/code/universe_3.R')
    # tdv = main_helper('/projects/bdata/kenqgu/Research/MultiverseProject/MultiverseTooling/multiverse-tooling/data/playing_around_r/multiverse/code/universe_10.R')
    # tdv = main_helper('/projects/bdata/kenqgu/Research/MultiverseProject/MultiverseTooling/multiverse-tooling/data/playing_around_python/multiverse/code/universe_9.py')
    tdv.get_all_config()
    print('here')