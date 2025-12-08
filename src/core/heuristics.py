from __future__ import annotations

import math
from typing import Dict, List, Sequence

from .distance import haversine
from .vrp import Node


def nearest_neighbor_order(node_ids: Sequence[int], nodes: Dict[int, Node], depot: Node) -> List[int]:
    remaining = set(node_ids)
    order: List[int] = []
    current = depot.node_id
    while remaining:
        next_node = min(remaining, key=lambda nid: haversine(nodes[current].coord, nodes[nid].coord))
        order.append(next_node)
        remaining.remove(next_node)
        current = next_node
    return order


def trivial_sa_placeholder(order: Sequence[int]) -> List[int]:
    """Placeholder for SA; currently returns same order to keep interface stable."""
    return list(order)
