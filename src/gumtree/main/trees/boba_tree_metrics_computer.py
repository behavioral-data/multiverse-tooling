
from src.gumtree.main.trees.tree import Tree
from src.gumtree.main.trees.tree_metrics import BobaTreeMetrics
from src.gumtree.main.trees.tree_visitor import TreeMetricComputer

from src.gumtree.main.trees.node_constants import BOBA_VAR


class BobaTreeMetricsComptuer(TreeMetricComputer):
    def visit_leaf(self, tree: Tree):
        num_child_boba_var_nodes = tree.num_boba_var_nodes
        num_child_boba_vars = 1 if tree.node_type == BOBA_VAR else 0
        
        tree.tree_metrics = BobaTreeMetrics(size=1,
                                            height=0, 
                                            hashcode=self.leaf_hash(tree),
                                            structure_hash=self.leaf_structure_hash(tree),
                                            depth=self.current_depth,
                                            position=self.current_position,
                                            num_child_boba_var_nodes=num_child_boba_var_nodes,
                                            num_child_boba_vars=num_child_boba_vars,
                                            height_from_child_boba_var=0
                                            )
        
    def end_inner_node(self, tree: Tree):
        self.current_depth -= 1
        sum_size = 0
        max_height = 0
        current_hash = 0
        current_structure_hash = 0
        sum_child_boba_var_nodes = 0
        sum_num_child_boba_vars = 0
        heights_from_boba_vars = []
        for child in tree.children: 
            metrics: BobaTreeMetrics = child.tree_metrics
            exponent = 2 * sum_size + 1
            current_hash += metrics.hashcode * self.hash_factor(exponent)
            current_structure_hash += metrics.structure_hash * self.hash_factor(exponent)
            sum_size += metrics.size
            if metrics.height > max_height:
                max_height = metrics.height
            sum_child_boba_var_nodes += metrics.num_child_boba_var_nodes
            sum_num_child_boba_vars += metrics.num_child_boba_vars
            if metrics.num_child_boba_vars > 0:
                heights_from_boba_vars.append(metrics.height_from_child_boba_var)
            
        tree.tree_metrics = BobaTreeMetrics(size=sum_size + 1,
                                        height=max_height + 1,
                                        hashcode=self.inner_node_hash(tree, 2 * sum_size + 1, current_hash),
                                        structure_hash=self.inner_node_structure_hash(tree, 2 * sum_size + 1, current_structure_hash),
                                        depth=self.current_depth,
                                        position=self.current_position,
                                        num_child_boba_vars=sum_num_child_boba_vars,
                                        num_child_boba_var_nodes=sum_child_boba_var_nodes,
                                        height_from_child_boba_var=min(heights_from_boba_vars) + 1 if heights_from_boba_vars else 0
        )
        self.current_position += 1