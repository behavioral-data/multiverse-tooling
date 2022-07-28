
from dataclasses import dataclass

@dataclass
class TreeMetrics:
    size: int
    height: int
    hashcode: int
    structure_hash: int
    depth: int
    position: int

@dataclass
class BobaTreeMetrics(TreeMetrics):
    num_child_boba_var_nodes: int
    num_child_boba_vars: int 
    height_from_child_boba_var: int