from __future__ import annotations

from typing import Dict, List, Sequence

from .vrp import RouteMetrics, VRPParams, WeightParams, split_routes, compute_route_metrics, Node


def evaluate_individual(
    permutation: Sequence[int],
    nodes_map: Dict[int, Node],
    depot: Node,
    vrp: VRPParams,
    weights: WeightParams,
) -> tuple[float, List[RouteMetrics]]:
    routes = split_routes(permutation, nodes_map, depot, vrp)
    route_metrics: List[RouteMetrics] = []
    total_distance = 0.0
    total_penalty = {"capacity": 0.0, "range": 0.0, "priority": 0.0, "time": 0.0}
    for route in routes:
        metrics = compute_route_metrics(route, nodes_map, depot, vrp, weights)
        route_metrics.append(metrics)
        total_distance += metrics.distance_km
        for key, val in metrics.penalties.items():
            total_penalty[key] += val

    fitness = (
        weights.w_distance * total_distance
        + weights.w_capacity * total_penalty["capacity"]
        + weights.w_range * total_penalty["range"]
        + weights.w_priority * total_penalty["priority"]
        + weights.w_time * total_penalty["time"]
    )
    return fitness, route_metrics
