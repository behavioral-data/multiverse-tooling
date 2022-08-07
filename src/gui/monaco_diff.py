from typing import List
from src.boba.parser import Parser

import os.path as osp
from src.gumtree.main.client.boba_template_diff import TemplateDiff
from src.gumtree.main.trees.tree import Tree


class TemplateDiffView:
    def __init__(self, ps: Parser, dst_file: str):
        universe_num = int(osp.basename(dst_file).split('.')[0].split('_')[-1])
        with open(dst_file, 'r') as f:
            universe_code = f.read()
        self.template_diff: TemplateDiff = TemplateDiff(ps, universe_code, universe_num)
        self.template_code_pos = self.template_diff.template_code_pos
        self.new_template_code_pos = self.template_diff.template_builder.new_template_code_pos
    
    def get_all_config(self):
        return ('config = {{ file: "{}", newUniverse: {}, '
                'oldTemplate: {}, newTemplate: {}, '
                'templateMappings: {}, newUniTemplateMappings: {}}};'.format('test.py', 
                                                                             self.get_new_universe_js_config(),
                                                                             self.get_old_template_js_config(),
                                                                             self.get_new_template_js_config(),
                                                                             self.get_templates_mapped_js_config(),
                                                                             self.get_new_universe_new_template_mapped_js_config()))
        
    def get_new_universe_js_config(self):
        c = self.template_diff.classifier
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
            boba_conf_offset = self.new_template_code_pos.get_boba_config_pos_offset()
            if t in c_spec.get_moved_dsts():
                self.append_range(b, t, kind="moved", offset=boba_conf_offset)
            if t in c_spec.get_updated_dsts():
                self.append_range(b, t, kind="updated", offset=boba_conf_offset)
            if t in c_spec.get_inserted_dsts():
                self.append_range(b, t, kind="inserted", offset=boba_conf_offset)

        inter_prime_preorder = self.template_diff.new_intermediary_tree.pre_order()
        for t in self.template_diff.diff.dst.root.pre_order():
            inter_tree = next(inter_prime_preorder)
            offset = self.new_template_code_pos.get_pos_offset(t)
            if t in c.get_moved_dsts():
                self.append_range(b, inter_tree, kind="moved", offset=offset)
            if t in c.get_updated_dsts():
                self.append_range(b, inter_tree, kind="updated", offset=offset)
            if t in c.get_inserted_dsts():
                self.append_range(b, inter_tree, kind="inserted", offset=offset)
        b.append("],")
        b.append("}")
        return " ".join(b)
        
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
            offset = self.template_code_pos.get_pos_offset(t)
            if t in c.get_moved_srcs():
                self.append_range(b, t, kind="moved", offset=offset)
            if t in c.get_updated_srcs():
                self.append_range(b, t, kind="updated", offset=offset)
            if t in c.get_deleted_srcs():
                self.append_range(b, t, kind="deleted", offset=offset)
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
                offset_new_template = self.new_template_code_pos.get_boba_config_pos_offset()
                b.append("[{}, {}, {}, {}],".format(t.pos + offset_template,
                                                   t.end_pos + offset_template,
                                                   d.pos + offset_new_template,
                                                   d.end_pos + offset_new_template))
        for t in self.template_diff.diff.src.root.pre_order():
            if t in c.get_moved_srcs() or t in c.get_updated_srcs():
                d = self.template_diff.diff.mappings.get_dst_for_src(t)
                offset_template = self.template_code_pos.get_pos_offset(t)
                offset_new_template = self.new_template_code_pos.get_pos_offset(d)
                b.append("[{}, {}, {}, {}],".format(t.pos + offset_template,
                                                   t.end_pos + offset_template,
                                                   d.pos + offset_new_template,
                                                   d.end_pos + offset_new_template))
                
        b.append("]")
        return " ".join(b)
    
    def get_new_universe_new_template_mapped_js_config(self):
        c = self.template_diff.classifier
        b = ["["]
        for t in self.template_diff.diff.dst.root.pre_order():
            if t in c.get_moved_dsts() or t in c.get_inserted_dsts() or t in c.get_updated_dsts():
                offset = self.new_template_code_pos.get_pos_offset(t)
                b.append("[{}, {}, {}, {}],".format(t.pos,
                                                    t.end_pos,
                                                    t.pos + offset,
                                                    t.end_pos + offset))
        b.append("],")
        return " ".join(b)
                
            
    def append_range(self, b: List[str], t: Tree, kind: str, offset: int=None):
        if offset is None:
            offset = 0
        b.append("{")
        b.append(f"from: {t.pos + offset},")
        b.append(f"to: {t.end_pos + offset},")
        b.append(f"index: {t.tree_metrics.depth},")
        b.append(f'kind: "{kind}",')
        b.append(f'tooltip: "{self.tooltip(t)}",')
        b.append("},")
    

    def tooltip(self, t: Tree):
        if t.parent is None:
            return t.node_type
        else:
            return t.parent.node_type + "/" + t.node_type
        
if __name__ == "__main__":
    from src.utils import load_parser_example, DATA_DIR
    import os.path as osp
    dataset, ext = 'fertility2', 'py'
    save_file = osp.join(DATA_DIR, f'{dataset}_template_parser_obj_0804.pickle')
    ps = load_parser_example(dataset, ext, save_file, run_parser_main=True)
    tdv = TemplateDiffView(ps, osp.join(DATA_DIR, dataset, 'multiverse', 'code', 'universe_3.py'))
    s4 = tdv.get_all_config()
    print('here')