from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


def ensure_parent(path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def save_json(data: Dict[str, Any], path: str | Path) -> None:
    p = ensure_parent(path)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def save_md(text: str, path: str | Path) -> None:
    p = ensure_parent(path)
    p.write_text(text, encoding="utf-8")


def save_log_records(records: List[Dict[str, Any]], path: str | Path) -> None:
    p = ensure_parent(path)
    with p.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def save_convergence(convergence: List[float], path: str | Path) -> None:
    p = ensure_parent(path)
    pd.Series(convergence).to_csv(p, index_label="generation", header=["best_fitness"])
