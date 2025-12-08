from __future__ import annotations

from typing import List

import matplotlib.pyplot as plt


def plot_convergence(convergence: List[float], path: str) -> None:
    plt.figure(figsize=(6, 4))
    plt.plot(convergence, label="best fitness")
    plt.xlabel("Generation")
    plt.ylabel("Fitness (lower is better)")
    plt.title("GA Convergence")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
