from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd

from src.core.vrp import Node


def load_nodes(path: str | Path) -> Dict[int, Node]:
    df = pd.read_csv(path)
    nodes: Dict[int, Node] = {}
    for _, row in df.iterrows():
        node = Node(
            node_id=int(row["id"]),
            name=row["nome"],
            state=row.get("estado", ""),
            lat=float(row["latitude"]),
            lon=float(row["longitude"]),
            demand=float(row.get("demanda", 0)),
            priority=int(row.get("prioridade", 1)),
            window_start=row.get("janela_inicio") if isinstance(row.get("janela_inicio"), str) else None,
            window_end=row.get("janela_fim") if isinstance(row.get("janela_fim"), str) else None,
            service_time_min=int(row.get("tempo_atendimento_min", 0)),
        )
        nodes[node.node_id] = node
    return nodes


def validate_nodes(nodes: Dict[int, Node]) -> List[str]:
    errors: List[str] = []
    if not nodes:
        errors.append("Dataset vazio")
    seen = set()
    for node_id, node in nodes.items():
        if node_id in seen:
            errors.append(f"ID duplicado: {node_id}")
        seen.add(node_id)
        if not (-90 <= node.lat <= 90 and -180 <= node.lon <= 180):
            errors.append(f"Coordenada inválida para {node.name}")
        if node.priority not in (1, 2, 3):
            errors.append(f"Prioridade inválida {node.priority} para {node.name}")
    return errors
