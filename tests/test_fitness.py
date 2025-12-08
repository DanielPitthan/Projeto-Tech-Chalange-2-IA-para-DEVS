from src.core.fitness import evaluate_individual
from src.core.vrp import Node, VRPParams, WeightParams


def test_fitness_penalizes_capacity():
    nodes = {
        0: Node(0, "Depot", "", 0, 0, 0, 1),
        1: Node(1, "A", "", 0, 1, 100, 1),
        2: Node(2, "B", "", 1, 1, 100, 1),
    }
    vrp = VRPParams(
        vehicles=1,
        vehicle_capacity=50,
        vehicle_range_km=10000,
        vehicle_speed_kmh=60,
        service_time_min=0,
        work_time_window=None,
    )
    weights = WeightParams(1, 10, 1, 1, 1)
    fitness, routes = evaluate_individual([1, 2], nodes, nodes[0], vrp, weights)
    assert fitness > 0
    assert routes[0].penalties["capacity"] > 0
