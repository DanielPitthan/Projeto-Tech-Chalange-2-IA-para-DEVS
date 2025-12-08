import random

from src.core.selection import roulette_selection, tournament_selection


def test_tournament_best_selected():
    pop = [[1], [2], [3]]
    fitness = [3, 2, 1]
    random.seed(0)
    selected = tournament_selection(pop, fitness, k=2)
    assert selected in pop


def test_roulette_returns_individual():
    pop = [[1], [2], [3]]
    fitness = [1, 2, 3]
    random.seed(1)
    selected = roulette_selection(pop, fitness)
    assert selected in pop
