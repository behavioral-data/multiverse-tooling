from typing import List
from src.boba.parser import Parser

import os.path as osp
from src.gumtree.main.client.boba_template_diff import TemplateDiff
from src.gumtree.main.trees.tree import Tree


class TemplateDiffView:
    def __init__(self, ps: Parser, dst_file: str):
        universe_num = int(osp.basename(dst_file).split('.')[0].split('_')[-1])
        self.dst_file = dst_file
        with open(dst_file, 'r') as f:
            universe_code = f.read()
        self.template_diff: TemplateDiff = TemplateDiff(ps, universe_code, universe_num)
        self.template_code_pos = self.template_diff.template_code_pos
        self.new_template_code_pos = self.template_diff.template_builder.new_template_code_pos
    
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
    
    def get_new_universe_mapped_boba_nodes_from_spec_tree(self, t: Tree) -> List[Tree]:
        new_choice_spec_tree, child_url = self.get_boba_var_choice_tree_from_child(t)
        pos_in_parent = new_choice_spec_tree.position_in_parent()
        old_choice_spec_tree = self.template_diff.spec_diff.mappings.get_src_for_dst(new_choice_spec_tree.parent).children[pos_in_parent]
        boba_var = self.template_diff.template_spec_tree_to_boba_choice_var[old_choice_spec_tree]
        ret = []    
        for dst_node in self.template_diff.diff.mappings.boba_var_to_dst_nodes[boba_var]:
            if child_url:
                ret.append(dst_node.get_child_from_url(child_url))
            else:
                ret.append(dst_node)
        return ret
    
    def get_new_universe_js_config(self):
        c = self.template_diff.classifier
        c_spec = self.template_diff.spec_classifier

        b: List[str] = []
        b.append("{")
        b.append("url:")
        b.append('"/new_universe",')
        b.append("ranges: [")
        for t in self.template_diff.spec_diff.dst.root.pre_order():
            if c_spec.changed_dst_tree(t):
                nodes = self.get_new_universe_mapped_boba_nodes_from_spec_tree(t)
                for node in nodes:
                    if t in c_spec.get_moved_dsts():
                        self.append_range(b, node, kind="moved")
                    if t in c_spec.get_updated_dsts():
                        self.append_range(b, node, kind="updated")
                    if t in c_spec.get_inserted_dsts():
                        self.append_range(b, node, kind="inserted")

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
        c_spec = self.template_diff.spec_classifier
        b = ["["]
        for t in self.template_diff.spec_diff.dst.root.pre_order():
            if c_spec.changed_dst_tree(t):
                nodes = self.get_new_universe_mapped_boba_nodes_from_spec_tree(t)
                for node in nodes:
                    b.append("[{}, {}, {}, {}],".format(node.pos,
                                                        node.end_pos,
                                                        t.pos,
                                                        t.end_pos))
                        
        for t in self.template_diff.diff.dst.root.pre_order():
            if t in c.get_moved_dsts() or t in c.get_inserted_dsts() or t in c.get_updated_dsts():
                offset = self.new_template_code_pos.get_pos_offset(t)
                b.append("[{}, {}, {}, {}],".format(t.pos,
                                                    t.end_pos,
                                                    t.pos + offset,
                                                    t.end_pos + offset))
        b.append("]")
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
    
    tdv = main_helper('/projects/bdata/kenqgu/Research/MultiverseProject/MultiverseTooling/multiverse-tooling/data/fertility_08082022/multiverse/code/universe_3.py')
    tdv.get_all_config()
    print('here')