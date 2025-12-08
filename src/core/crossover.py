from __future__ import annotations

import random
from typing import List, Sequence, Tuple

Individual = List[int]


def pmx(parent1: Sequence[int], parent2: Sequence[int]) -> Tuple[Individual, Individual]:
    size = len(parent1)
    p1, p2 = [None] * size, [None] * size
    idx1, idx2 = sorted(random.sample(range(size), 2))

    p1[idx1:idx2] = parent1[idx1:idx2]
    p2[idx1:idx2] = parent2[idx1:idx2]

    def fill_child(child, parent_a, parent_b):
        for i in range(idx1, idx2):
            if parent_b[i] not in child:
                pos = i
                val = parent_a[i]
                while True:
                    try:
                        pos = parent_b.index(val)
                    except ValueError:
                        break
                    if child[pos] is None:
                        break
                    val = parent_a[pos]
                child[pos] = parent_b[i]
        for i in range(size):
            if child[i] is None:
                child[i] = parent_b[i]
        return child

    c1 = fill_child(p1, parent1, parent2)
    c2 = fill_child(p2, parent2, parent1)
    return c1, c2


def ox(parent1: Sequence[int], parent2: Sequence[int]) -> Tuple[Individual, Individual]:
    size = len(parent1)
    idx1, idx2 = sorted(random.sample(range(size), 2))

    def make_child(p_a, p_b):
        child = [None] * size
        child[idx1:idx2] = p_a[idx1:idx2]
        pos = idx2
        for gene in p_b[idx2:] + p_b[:idx2]:
            if gene not in child:
                if pos >= size:
                    pos = 0
                child[pos] = gene
                pos += 1
        return child

    return make_child(parent1, parent2), make_child(parent2, parent1)
