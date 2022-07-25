
from dataclasses import dataclass

@dataclass
class TreeMetrics:
    size: int
    height: int
    hashcode: int
    structure_hash: int
    depth: int
    position: int