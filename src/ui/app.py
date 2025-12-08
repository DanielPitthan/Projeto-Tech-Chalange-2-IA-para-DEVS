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

    # Sidebar for API key and settings
    with st.sidebar:
        st.header("⚙️ Configurações")
        provider = st.selectbox("Provider LLM", ["openai", "gemini", "local"], index=0)
        model_input = st.text_input(
            "Modelo",
            value="gpt-4o-mini" if provider == "openai" else "gemini-1.5-flash",
            help="Ex.: openai: gpt-4o-mini / gpt-3.5-turbo | gemini: gemini-1.5-flash"
        )
        api_key_input = st.text_input(
            "API Key (opcional)",
            type="password",
            help="Deixe em branco para usar variável de ambiente: OPENAI_API_KEY ou GEMINI_API_KEY"
        )
        st.caption("⚠️ **Nunca compartilhe sua chave**. Revogue chaves expostas em seus painéis do provedor.")
        st.divider()
        st.markdown("### 💡 Dicas")
        st.markdown("""
        - OpenAI: gpt-4o-mini ou gpt-3.5-turbo (mais barato)
        - Gemini: gemini-1.5-flash ou gemini-1.5-pro
        - Local: usa stub interno (sem custo)
        """)

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
        map_html = build_map_html(routes, cfg.depot, {cfg.depot.node_id: cfg.depot, **load_nodes(data_path)})
        st.components.v1.html(map_html, height=600)

        # LLM instructions for first route
        api_key = api_key_input.strip()
        if not api_key:
            # try provider-specific env vars
            if provider == "openai":
                api_key = os.environ.get("OPENAI_API_KEY", "")
            elif provider == "gemini":
                api_key = os.environ.get("GEMINI_API_KEY", "")
            else:
                api_key = ""
        if api_key and solution["routes"]:
            st.subheader("📝 Instruções operacionais (LLM)")
            try:
                client = LLMClient(
                    model_input or cfg.llm.get("model", "gpt-4o-mini"),
                    api_key=api_key,
                    temperature=cfg.llm.get("temperature", 0.2),
                    provider=provider,
                )
                instr = instructions_for_route(client, solution["routes"][0]["vehicle_id"], solution["routes"][0])
                st.markdown(instr)
            except Exception as e:
                st.error(f"❌ Erro ao chamar LLM: {e}")
                st.info("� **Soluções**: Verifique créditos em [Billing](https://platform.openai.com/account/billing) ou troque o modelo no `config.yaml` para `gpt-3.5-turbo` ou `gpt-4o-mini`")
        else:
            st.info("💡 Forneça uma API key na barra lateral ou defina `OPENAI_API_KEY` / `GEMINI_API_KEY` no ambiente para habilitar instruções LLM.")

    st.caption("Execute: `streamlit run src/ui/app.py`")


if __name__ == "__main__":
    main()
