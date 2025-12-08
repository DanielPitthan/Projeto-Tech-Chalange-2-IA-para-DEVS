from __future__ import annotations

import random
from typing import Dict, List, Sequence, Tuple

from .crossover import ox, pmx
from .fitness import evaluate_individual
from .mutation import mutate
from .selection import select_pair
from .vrp import GAParams, Node, VRPParams, WeightParams

Individual = List[int]


class GeneticAlgorithm:
    def __init__(
        self,
        nodes_map: Dict[int, Node],
        depot: Node,
        ga_params: GAParams,
        vrp_params: VRPParams,
        weights: WeightParams,
    ) -> None:
        self.nodes_map = nodes_map
        self.depot = depot
        self.ga = ga_params
        self.vrp = vrp_params
        self.weights = weights
        if self.ga.seed is not None:
            random.seed(self.ga.seed)

    def initial_population(self, base_orders: List[Sequence[int]]) -> List[Individual]:
        population: List[Individual] = []
        node_ids = [nid for nid in self.nodes_map if nid != self.depot.node_id]
        for _ in range(self.ga.population_size - len(base_orders)):
            indiv = node_ids[:]
            random.shuffle(indiv)
            population.append(indiv)
        population.extend([list(order) for order in base_orders])
        return population[: self.ga.population_size]

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        if random.random() > self.ga.crossover_rate:
            return parent1[:], parent2[:]
        if self.ga.crossover.upper() == "PMX":
            return pmx(parent1, parent2)
        if self.ga.crossover.upper() == "OX":
            return ox(parent1, parent2)
        raise ValueError(f"Unsupported crossover {self.ga.crossover}")

    def evolve(self, population: List[Individual]) -> Tuple[List[Individual], List[float], List[List]]:
        fitness_values: List[float] = []
        decoded_routes: List[List] = []
        for indiv in population:
            fit, routes = evaluate_individual(indiv, self.nodes_map, self.depot, self.vrp, self.weights)
            fitness_values.append(fit)
            decoded_routes.append(routes)

        new_population: List[Individual] = []
        # Elitism
        elite_indices = sorted(range(len(population)), key=lambda i: fitness_values[i])[: self.ga.elitism]
        for idx in elite_indices:
            new_population.append(population[idx])

        while len(new_population) < self.ga.population_size:
            parent1, parent2 = select_pair(
                population, fitness_values, self.ga.selection, self.ga.tournament_k
            )
            child1, child2 = self.crossover(parent1, parent2)
            if random.random() < self.ga.mutation_rate:
                child1 = mutate(child1, self.ga.mutation)
            if random.random() < self.ga.mutation_rate:
                child2 = mutate(child2, self.ga.mutation)
            new_population.append(child1)
            if len(new_population) < self.ga.population_size:
                new_population.append(child2)
        return new_population, fitness_values, decoded_routes

    def run(self, base_orders: List[Sequence[int]]) -> Tuple[Individual, float, List[float], List[List]]:
        population = self.initial_population(base_orders)
        best_fitness = float("inf")
        best_individual: Individual | None = None
        convergence: List[float] = []
        decoded_history: List[List] = []
        stagnant = 0

        for gen in range(self.ga.generations):
            population, fitness_vals, decoded = self.evolve(population)
            decoded_history = decoded
            gen_best_idx = min(range(len(fitness_vals)), key=lambda i: fitness_vals[i])
            gen_best_fit = fitness_vals[gen_best_idx]
            if gen_best_fit < best_fitness:
                best_fitness = gen_best_fit
                best_individual = population[gen_best_idx]
                stagnant = 0
            else:
                stagnant += 1
            convergence.append(gen_best_fit)
            if stagnant >= self.ga.stagnation_patience:
                break
        assert best_individual is not None
        return best_individual, best_fitness, convergence, decoded_history
