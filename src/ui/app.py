from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Ensure project root is on sys.path so `import src.*` works when running via streamlit
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import folium
import matplotlib.pyplot as plt
import streamlit as st

from src.cli import build_solution_json
from src.core.fitness import evaluate_individual
from src.core.ga import GeneticAlgorithm
from src.core.heuristics import nearest_neighbor_order
from src.core.vrp import Node
from src.io.config import ConfigLoader
from src.io.load_data import load_nodes, validate_nodes
from src.llm.render import LLMClient, instructions_for_route


def build_map_html(routes, depot: Node, nodes: Dict[int, Node]) -> str:
    m = folium.Map(location=[depot.lat, depot.lon], zoom_start=4)
    folium.Marker(
        [depot.lat, depot.lon], popup=f"Depot: {depot.name}", icon=folium.Icon(color="black")
    ).add_to(m)
    for node in nodes.values():
        if node.node_id == depot.node_id:
            continue
        color = "red" if node.priority == 1 else "orange" if node.priority == 2 else "blue"
        folium.CircleMarker(
            [node.lat, node.lon], radius=4, color=color, fill=True, popup=f"{node.name} (p{node.priority})"
        ).add_to(m)
    for idx, route in enumerate(routes):
        color = [
            "red",
            "blue",
            "green",
            "purple",
            "orange",
            "darkred",
            "lightred",
            "beige",
            "darkblue",
            "darkgreen",
            "cadetblue",
            "darkpurple",
        ][idx % 12]
        coords = [[nodes[nid].lat, nodes[nid].lon] for nid in route.sequence]
        folium.PolyLine(coords, color=color, weight=4, opacity=0.8).add_to(m)
    return m._repr_html_()


def plot_convergence_fig(convergence: List[float]) -> bytes:
    plt.figure(figsize=(6, 3))
    plt.plot(convergence, label="best fitness")
    plt.xlabel("Generation")
    plt.ylabel("Fitness")
    plt.legend()
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return buf.read()


def run_optimizer(config_path: str, data_path: str):
    cfg = ConfigLoader.load(config_path)
    nodes = load_nodes(data_path)
    errors = validate_nodes(nodes)
    if errors:
        raise ValueError("; ".join(errors))

    nodes_with_depot = {cfg.depot.node_id: cfg.depot, **nodes}
    base_orders = [
        nearest_neighbor_order(
            [n for n in nodes_with_depot if n != cfg.depot.node_id], nodes_with_depot, cfg.depot
        )
    ]
    ga = GeneticAlgorithm(nodes_with_depot, cfg.depot, cfg.ga, cfg.vrp, cfg.weights)
    best_indiv, best_fit, convergence, _ = ga.run(base_orders)
    fitness_val, routes = evaluate_individual(best_indiv, nodes_with_depot, cfg.depot, cfg.vrp, cfg.weights)
    solution_json = build_solution_json(routes, convergence, cfg.depot, nodes_with_depot, fitness_val)
    return solution_json, routes, convergence, cfg


def main():
    st.set_page_config(page_title="Cacheiro VRP GA", layout="wide")
    st.title("🚑 Cacheiro VRP GA - Dashboard")

    # Sidebar for LLM settings (Ollama local only)
    with st.sidebar:
        st.header("⚙️ LLM (Ollama local)")
        model_input = st.text_input(
            "Modelo Ollama",
            value="llama3",
            help="Ex.: llama3, llama3.2:3b-instruct, qwen2.5, deepseek-r1, etc. Certifique-se de ter feito `ollama pull <modelo>`.",
        )
        host_input = st.text_input(
            "Host (opcional)",
            value=os.environ.get("OLLAMA_HOST", ""),
            help="Ex.: http://localhost:11434. Deixe em branco para usar o padrão do Ollama local.",
        )
        st.caption("💡 Rode `ollama serve` e `ollama pull <modelo>` antes de executar a otimização.")

    col1, col2 = st.columns(2)
    with col1:
        config_path = st.text_input("Config YAML", value="config.yaml")
    with col2:
        data_path = st.text_input("Dataset CSV", value="src/data/capitais.csv")

    if st.button("🚀 Executar otimização", type="primary"):
        with st.spinner("Rodando GA..."):
            try:
                solution, routes, convergence, cfg = run_optimizer(config_path, data_path)
            except Exception as e:  # pragma: no cover - UI feedback
                st.error(f"Erro: {e}")
                return

        st.success("✅ Otimização concluída!")

        gm = solution["global_metrics"]
        st.subheader("📊 Métricas globais")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Distância total (km)", f"{gm['distance_total_km']:.1f}")
        with col_m2:
            st.metric("Veículos usados", gm["vehicles_used"])
        with col_m3:
            st.metric("Melhor fitness", f"{gm['best_fitness']:.2f}")

        st.subheader("🚛 Rotas")
        st.json(solution["routes"], expanded=False)

        st.subheader("📈 Convergência")
        png = plot_convergence_fig(convergence)
        st.image(png)

        st.subheader("🗺️ Mapa")
        nodes_map_ui = {cfg.depot.node_id: cfg.depot, **load_nodes(data_path)}
        map_html = build_map_html(routes, cfg.depot, nodes_map_ui)
        st.components.v1.html(map_html, height=600)

        # LLM instructions for first route (Ollama local)
        if solution["routes"]:
            st.subheader("📝 Instruções operacionais (LLM - Ollama)")
            try:
                client = LLMClient(
                    model_input or cfg.llm.get("model", "llama3"),
                    temperature=cfg.llm.get("temperature", 0.2),
                    host=host_input or cfg.llm.get("host"),
                )
                instr = instructions_for_route(
                    client=client,
                    route=solution["routes"][0],
                    nodes_map=nodes_map_ui,
                    depot=cfg.depot,
                    departure_time=cfg.llm.get("departure_time", "08:00"),
                    vehicle_speed_kmh=cfg.vrp.vehicle_speed_kmh,
                )
                st.markdown(instr)
            except Exception as e:
                st.error(f"❌ Erro ao chamar LLM (Ollama): {e}")
                st.info("💡 Verifique se o serviço Ollama está rodando (`ollama serve`) e se o modelo foi baixado (`ollama pull <modelo>`).")
        else:
            st.info("💡 Nenhuma rota gerada para solicitar instruções ao LLM.")

    st.caption("Execute: `streamlit run src/ui/app.py`")


if __name__ == "__main__":
    main()
