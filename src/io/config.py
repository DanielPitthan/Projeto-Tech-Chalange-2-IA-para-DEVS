from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml

from src.core.vrp import GAParams, VRPParams, WeightParams, Node


@dataclass
class Config:
    ga: GAParams
    vrp: VRPParams
    weights: WeightParams
    depot: Node
    llm: Dict[str, Any]
    logging: Dict[str, Any]
    output: Dict[str, Any]


class ConfigLoader:
    @staticmethod
    def load(path: str | Path) -> Config:
        cfg = yaml.safe_load(Path(path).read_text())
        ga_cfg = cfg.get("ga", {})
        vrp_cfg = cfg.get("vrp", {})
        weights_cfg = cfg.get("weights", {})
        depot_cfg = cfg.get("depot", {})

        ga = GAParams(
            population_size=ga_cfg.get("population_size", 100),
            generations=ga_cfg.get("generations", 200),
            selection=ga_cfg.get("selection", "tournament"),
            tournament_k=ga_cfg.get("tournament_k", 3),
            crossover=ga_cfg.get("crossover", "PMX"),
            crossover_rate=float(ga_cfg.get("crossover_rate", 0.9)),
            mutation=ga_cfg.get("mutation", "swap"),
            mutation_rate=float(ga_cfg.get("mutation_rate", 0.1)),
            elitism=int(ga_cfg.get("elitism", 2)),
            stagnation_patience=int(ga_cfg.get("stagnation_patience", 30)),
            seed=ga_cfg.get("seed"),
        )
        vrp = VRPParams(
            vehicles=int(vrp_cfg.get("vehicles", 3)),
            vehicle_capacity=float(vrp_cfg.get("vehicle_capacity", 100)),
            vehicle_range_km=float(vrp_cfg.get("vehicle_range_km", 800)),
            vehicle_speed_kmh=float(vrp_cfg.get("vehicle_speed_kmh", 50)),
            service_time_min=float(vrp_cfg.get("service_time_min", 10)),
            work_time_window=vrp_cfg.get("work_time_window"),
        )
        weights = WeightParams(
            w_distance=float(weights_cfg.get("w_distance", 1.0)),
            w_capacity=float(weights_cfg.get("w_capacity", 50.0)),
            w_range=float(weights_cfg.get("w_range", 50.0)),
            w_priority=float(weights_cfg.get("w_priority", 10.0)),
            w_time=float(weights_cfg.get("w_time", 10.0)),
        )
        depot = Node(
            node_id=0,
            name=depot_cfg.get("name", "Deposito"),
            state=depot_cfg.get("estado", ""),
            lat=float(depot_cfg.get("latitude")),
            lon=float(depot_cfg.get("longitude")),
            demand=float(depot_cfg.get("demanda", 0)),
            priority=int(depot_cfg.get("prioridade", 1)),
            window_start=None,
            window_end=None,
            service_time_min=int(depot_cfg.get("tempo_atendimento_min", 0)),
        )
        return Config(
            ga=ga,
            vrp=vrp,
            weights=weights,
            depot=depot,
            llm=cfg.get("llm", {}),
            logging=cfg.get("logging", {}),
            output=cfg.get("output", {}),
        )
