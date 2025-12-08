import random

from src.core.crossover import ox, pmx
from src.core.mutation import inversion_mutation, swap_mutation


def test_pmx_preserves_genes():
    p1 = [1, 2, 3, 4, 5]
    p2 = [5, 4, 3, 2, 1]
    c1, c2 = pmx(p1, p2)
    assert sorted(c1) == sorted(p1)
    assert sorted(c2) == sorted(p2)


def test_ox_preserves_genes():
    p1 = [1, 2, 3, 4, 5]
    p2 = [5, 4, 3, 2, 1]
    c1, c2 = ox(p1, p2)
    assert sorted(c1) == sorted(p1)
    assert sorted(c2) == sorted(p2)


def test_swap_mutation_changes_two():
    random.seed(1)
    ind = [1, 2, 3, 4]
    mutated = swap_mutation(ind)
    assert sorted(mutated) == sorted(ind)
    assert mutated != ind


def test_inversion_mutation_reverses_segment():
    random.seed(2)
    ind = [1, 2, 3, 4, 5]
    mutated = inversion_mutation(ind)
    assert sorted(mutated) == sorted(ind)
    assert mutated != ind
