from __future__ import annotations

import argparse
import json
import os
import statistics
from typing import Dict, List

from src.core.ga import GeneticAlgorithm
from src.core.heuristics import nearest_neighbor_order
from src.core.vrp import Node
from src.io.config import ConfigLoader
from src.io.load_data import load_nodes, validate_nodes
from src.io.output_saver import save_convergence, save_json, save_log_records, save_md
from src.viz.charts import plot_convergence
from src.viz.map import render_map
from src.llm.render import LLMClient, executive_report, generate_all_instructions


def build_solution_json(routes, convergence, depot: Node, nodes: Dict[int, Node], fitness: float):
    vehicles_used = sum(1 for r in routes if len(r.sequence) > 2)
    distances = [r.distance_km for r in routes]
    loads = [r.load for r in routes]
    global_metrics = {
        "distance_total_km": sum(distances),
        "vehicles_used": vehicles_used,
        "distance_mean_km": statistics.mean(distances) if distances else 0,
        "distance_std_km": statistics.pstdev(distances) if len(distances) > 1 else 0,
        "load_mean": statistics.mean(loads) if loads else 0,
        "load_std": statistics.pstdev(loads) if len(loads) > 1 else 0,
        "best_fitness": fitness,
    }
    routes_json = []
    for idx, r in enumerate(routes):
        routes_json.append(
            {
                "vehicle_id": f"V{idx+1}",
                "sequence": r.sequence,
                "distance_km": r.distance_km,
                "time_min": r.time_min,
                "load": r.load,
                "penalties": r.penalties,
            }
        )
    feasibility = all(p == 0 for r in routes for p in r.penalties.values())
    return {
        "depot": {"id": depot.node_id, "name": depot.name},
        "routes": routes_json,
        "global_metrics": global_metrics,
        "convergence": [{"gen": i + 1, "best_fitness": v} for i, v in enumerate(convergence)],
        "feasibility": feasibility,
    }


def run():
    parser = argparse.ArgumentParser(description="GA VRP optimizer")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--data", required=True, help="Path to CSV dataset")
    args = parser.parse_args()

    cfg = ConfigLoader.load(args.config)
    nodes = load_nodes(args.data)
    errors = validate_nodes(nodes)
    if errors:
        raise SystemExit("; ".join(errors))

    # Garantir que o dicionário de nós contenha o depósito para uso em heurísticas e mapas
    nodes_with_depot = {cfg.depot.node_id: cfg.depot, **nodes}

    base_orders = [
        nearest_neighbor_order(
            [n for n in nodes_with_depot if n != cfg.depot.node_id], nodes_with_depot, cfg.depot
        )
    ]
    ga = GeneticAlgorithm(nodes_with_depot, cfg.depot, cfg.ga, cfg.vrp, cfg.weights)
    best_indiv, best_fit, convergence, decoded = ga.run(base_orders)

    # Recompute best routes for final individual
    from src.core.fitness import evaluate_individual

    fitness_val, routes = evaluate_individual(
        best_indiv, nodes_with_depot, cfg.depot, cfg.vrp, cfg.weights
    )

    solution_json = build_solution_json(routes, convergence, cfg.depot, nodes_with_depot, fitness_val)

    if cfg.output.get("solution_json"):
        save_json(solution_json, cfg.output["solution_json"])
    if cfg.output.get("convergence_png"):
        plot_convergence(convergence, cfg.output["convergence_png"])
    if cfg.output.get("map_html"):
        render_map(cfg.depot, nodes_with_depot, routes, cfg.output["map_html"])
    if cfg.logging.get("jsonl_path"):
        logs = [
            {"generation": i + 1, "best_fitness": v} for i, v in enumerate(convergence)
        ]
        save_log_records(logs, cfg.logging["jsonl_path"])

    # =========================================================================
    # GERAÇÃO DE CONTEÚDO VIA LLM
    # =========================================================================
    llm_config = getattr(cfg, "llm", None) or {}
    generate_instructions = llm_config.get("generate_instructions", False)
    generate_report = llm_config.get("generate_report", False)
    
    report_content = ""
    instructions_content = ""
    
    if generate_instructions or generate_report:
        # Inicializar cliente LLM
        llm_client = LLMClient(
            model=llm_config.get("model", "llama3"),
            temperature=llm_config.get("temperature", 0.2),
            host=llm_config.get("host"),
        )
        
        departure_time = llm_config.get("departure_time", "08:00")
        vehicle_speed = cfg.vrp.vehicle_speed_kmh if hasattr(cfg.vrp, "vehicle_speed_kmh") else 60.0
        
        if generate_instructions:
            print("\n[*] Gerando instrucoes para motoristas...")
            instructions_content = generate_all_instructions(
                client=llm_client,
                solution_json=solution_json,
                nodes_map=nodes_with_depot,
                depot=cfg.depot,
                departure_time=departure_time,
                vehicle_speed_kmh=vehicle_speed,
            )
            
            # Salvar instruções em arquivo separado
            instructions_path = cfg.output.get("report_md", "outputs/report.md").replace(".md", "_instructions.md")
            save_md(instructions_content, instructions_path)
            print(f"   [OK] Instrucoes salvas em: {instructions_path}")
        
        if generate_report:
            print("\n[*] Gerando relatorio executivo...")
            report_content = executive_report(
                client=llm_client,
                solution_json=solution_json,
                nodes_map=nodes_with_depot,
                depot=cfg.depot,
                baseline_json=None,  # TODO: carregar baseline de execução anterior se existir
            )
    
    # Salvar relatório (com ou sem LLM)
    if cfg.output.get("report_md"):
        if report_content:
            save_md(report_content, cfg.output["report_md"])
            print(f"   [OK] Relatorio salvo em: {cfg.output['report_md']}")
        else:
            # Fallback: salvar JSON formatado se LLM não estiver habilitado
            report = "# Resumo Executivo\n\n" + json.dumps(solution_json, indent=2, ensure_ascii=False)
            save_md(report, cfg.output["report_md"])

    print(json.dumps(solution_json, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run()
