from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Sequence, Tuple

from .distance import haversine, route_distance


@dataclass
class Node:
    node_id: int
    name: str
    state: str
    lat: float
    lon: float
    demand: float
    priority: int
    window_start: str | None = None
    window_end: str | None = None
    service_time_min: int = 0

    @property
    def coord(self) -> Tuple[float, float]:
        return (self.lat, self.lon)


@dataclass
class RouteMetrics:
    sequence: List[int]
    distance_km: float
    time_min: float
    load: float
    penalties: Dict[str, float]


@dataclass
class Solution:
    routes: List[RouteMetrics]
    global_metrics: Dict[str, float]
    convergence: List[Dict[str, float]]
    feasibility: bool


@dataclass
class GAParams:
    population_size: int
    generations: int
    selection: str
    tournament_k: int
    crossover: str
    crossover_rate: float
    mutation: str
    mutation_rate: float
    elitism: int
    stagnation_patience: int
    seed: int | None = None


@dataclass
class VRPParams:
    vehicles: int
    vehicle_capacity: float
    vehicle_range_km: float
    vehicle_speed_kmh: float
    service_time_min: float
    work_time_window: Sequence[str] | None = None


@dataclass
class WeightParams:
    w_distance: float
    w_capacity: float
    w_range: float
    w_priority: float
    w_time: float


def split_routes(
    permutation: Sequence[int],
    nodes_map: Dict[int, Node],
    depot: Node,
    vrp: VRPParams,
) -> List[List[int]]:
    """Greedy split of a permutation into routes respecting vehicle capacity as first cut."""
    routes: List[List[int]] = [[] for _ in range(vrp.vehicles)]
    loads = [0.0 for _ in range(vrp.vehicles)]
    vehicle_idx = 0
    for customer_id in permutation:
        demand = nodes_map[customer_id].demand
        if vehicle_idx >= vrp.vehicles:
            break
        if loads[vehicle_idx] + demand > vrp.vehicle_capacity and routes[vehicle_idx]:
            vehicle_idx += 1
        if vehicle_idx >= vrp.vehicles:
            break
        routes[vehicle_idx].append(customer_id)
        loads[vehicle_idx] += demand
    return routes


def compute_route_metrics(
    route: Sequence[int],
    nodes_map: Dict[int, Node],
    depot: Node,
    vrp: VRPParams,
    weights: WeightParams,
) -> RouteMetrics:
    sequence = [depot.node_id] + list(route) + [depot.node_id]
    coords = [nodes_map[idx].coord for idx in sequence]
    distance_km = route_distance(coords)
    # Travel time in minutes + service times
    travel_time_min = distance_km / max(vrp.vehicle_speed_kmh, 1e-6) * 60
    service_time_min = sum(nodes_map[idx].service_time_min for idx in route)
    time_min = travel_time_min + service_time_min
    load = sum(nodes_map[idx].demand for idx in route)

    penalties: Dict[str, float] = {"capacity": 0.0, "range": 0.0, "priority": 0.0, "time": 0.0}
    if load > vrp.vehicle_capacity:
        penalties["capacity"] = load - vrp.vehicle_capacity
    if distance_km > vrp.vehicle_range_km:
        penalties["range"] = distance_km - vrp.vehicle_range_km

    # Priority penalty: delay of critical (priority 1) deliveries based on position
    for pos, node_id in enumerate(route):
        node = nodes_map[node_id]
        if node.priority == 1:
            penalties["priority"] += pos  # earlier is better
        elif node.priority == 2:
            penalties["priority"] += 0.25 * pos
        else:
            penalties["priority"] += 0.1 * pos

    # Time window penalty (simplified earliest-start schedule)
    if vrp.work_time_window:
        start_str, end_str = vrp.work_time_window
        work_start = datetime.strptime(start_str, "%H:%M")
        work_end = datetime.strptime(end_str, "%H:%M")
        current_time = work_start
        for idx in route:
            node = nodes_map[idx]
            travel_minutes = haversine(depot.coord, node.coord) / max(vrp.vehicle_speed_kmh, 1e-6) * 60
            arrive = current_time + timedelta(minutes=travel_minutes)
            if node.window_start:
                window_start = datetime.strptime(node.window_start, "%H:%M")
                if arrive < window_start:
                    arrive = window_start
            if node.window_end:
                window_end = datetime.strptime(node.window_end, "%H:%M")
                if arrive > window_end:
                    penalties["time"] += (arrive - window_end).total_seconds() / 60
            arrive += timedelta(minutes=node.service_time_min)
            current_time = arrive
        if current_time > work_end:
            penalties["time"] += (current_time - work_end).total_seconds() / 60

    return RouteMetrics(
        sequence=sequence,
        distance_km=distance_km,
        time_min=time_min,
        load=load,
        penalties=penalties,
    )
