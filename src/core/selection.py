from __future__ import annotations

import random
from typing import List, Sequence, Tuple

Individual = Sequence[int]


def tournament_selection(population: List[Individual], fitness: List[float], k: int = 3) -> Individual:
    """Select best of k random individuals (lower fitness is better)."""
    indices = random.sample(range(len(population)), k)
    best_idx = min(indices, key=lambda idx: fitness[idx])
    return population[best_idx]


def roulette_selection(population: List[Individual], fitness: List[float]) -> Individual:
    """Roulette selection on inverted fitness (lower is better)."""
    max_fit = max(fitness)
    # Avoid division by zero: shift values up
    adjusted = [max_fit - f + 1e-6 for f in fitness]
    total = sum(adjusted)
    pick = random.uniform(0, total)
    current = 0.0
    for ind, weight in zip(population, adjusted):
        current += weight
        if current >= pick:
            return ind
    return population[-1]


def select_pair(
    population: List[Individual], fitness: List[float], method: str = "tournament", tournament_k: int = 3
) -> Tuple[Individual, Individual]:
    if method == "tournament":
        return (
            tournament_selection(population, fitness, tournament_k),
            tournament_selection(population, fitness, tournament_k),
        )
    if method == "roulette":
        return (
            roulette_selection(population, fitness),
            roulette_selection(population, fitness),
        )
    raise ValueError(f"Unsupported selection method: {method}")
