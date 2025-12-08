from __future__ import annotations

import random
from typing import List, Sequence

Individual = List[int]


def swap_mutation(individual: Sequence[int]) -> Individual:
    mutant = list(individual)
    i, j = random.sample(range(len(mutant)), 2)
    mutant[i], mutant[j] = mutant[j], mutant[i]
    return mutant


def inversion_mutation(individual: Sequence[int]) -> Individual:
    mutant = list(individual)
    i, j = sorted(random.sample(range(len(mutant)), 2))
    mutant[i:j] = reversed(mutant[i:j])
    return mutant


def mutate(individual: Sequence[int], method: str) -> Individual:
    if len(individual) < 2:
        return list(individual)
    if method.lower() == "swap":
        return swap_mutation(individual)
    if method.lower() == "inversion":
        return inversion_mutation(individual)
    raise ValueError(f"Unsupported mutation method: {method}")
