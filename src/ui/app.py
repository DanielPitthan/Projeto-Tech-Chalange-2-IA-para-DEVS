from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
from src.llm.render import LLMClient, instructions_for_route, navigation_instructions_for_route


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def list_ollama_models() -> Tuple[List[str], Optional[str]]:
    """
    Lista modelos disponíveis localmente no Ollama.
    
    Returns:
        Tuple[List[str], Optional[str]]: (lista de modelos, mensagem de erro se houver)
    """
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return [], f"Erro ao executar 'ollama list': {result.stderr}"
        
        # Parsear saída (formato: NAME ID SIZE MODIFIED)
        lines = result.stdout.strip().split("\n")
        models = []
        for line in lines[1:]:  # Pular header
            if line.strip():
                parts = line.split()
                if parts:
                    models.append(parts[0])  # Nome do modelo é a primeira coluna
        
        return models, None
    except FileNotFoundError:
        return [], "Ollama não encontrado. Instale em https://ollama.ai"
    except subprocess.TimeoutExpired:
        return [], "Timeout ao listar modelos Ollama"
    except Exception as e:
        return [], f"Erro inesperado: {e}"


def get_gpu_info() -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    """
    Detecta informações da GPU via nvidia-smi.
    
    Returns:
        Tuple[Optional[Dict], Optional[str]]: (info da GPU, mensagem de erro se houver)
    """
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None, "nvidia-smi falhou"
        
        # Parsear saída
        line = result.stdout.strip().split("\n")[0]
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3:
            return {
                "name": parts[0],
                "memory_total_mb": parts[1],
                "memory_free_mb": parts[2],
            }, None
        return None, "Formato inesperado de nvidia-smi"
    except FileNotFoundError:
        return None, "nvidia-smi não encontrado (GPU NVIDIA não detectada)"
    except subprocess.TimeoutExpired:
        return None, "Timeout ao consultar GPU"
    except Exception as e:
        return None, f"Erro: {e}"


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


def run_optimizer(config_path: str, data_path: str, num_vehicles: Optional[int] = None):
    """Executa o otimizador GA.
    
    Args:
        config_path: Caminho para o arquivo de configuração YAML
        data_path: Caminho para o arquivo CSV de dados
        num_vehicles: Número de veículos (sobrescreve config se informado)
    """
    cfg = ConfigLoader.load(config_path)
    
    # Sobrescrever número de veículos se informado pela UI
    if num_vehicles is not None:
        cfg.vrp.vehicles = num_vehicles
    
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

    # =========================================================================
    # SIDEBAR: Configurações de LLM e GPU
    # =========================================================================
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # --- GPU Info e Toggle ---
        st.subheader("🖥️ GPU")
        gpu_info, gpu_error = get_gpu_info()
        
        if gpu_info:
            st.success(f"✅ **{gpu_info['name']}**")
            st.caption(f"Memória: {gpu_info['memory_total_mb']} MB total, {gpu_info['memory_free_mb']} MB livre")
            use_gpu = st.checkbox("Usar GPU para LLM", value=True, help="Desmarque para forçar uso de CPU")
        else:
            st.warning("⚠️ CPU only")
            st.caption(gpu_error or "GPU não detectada")
            use_gpu = False
            st.checkbox("Usar GPU para LLM", value=False, disabled=True)
        
        # Configurar variável de ambiente para GPU
        if not use_gpu:
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
        elif "CUDA_VISIBLE_DEVICES" in os.environ and os.environ["CUDA_VISIBLE_DEVICES"] == "":
            del os.environ["CUDA_VISIBLE_DEVICES"]
        
        st.divider()
        
        # --- LLM: Modelos Ollama ---
        st.subheader("🤖 LLM (Ollama)")
        
        models, models_error = list_ollama_models()
        
        if models:
            selected_model = st.selectbox(
                "Modelo disponível",
                options=models,
                index=0,
                help="Modelos instalados localmente via 'ollama pull'"
            )
            model_input = selected_model
        else:
            st.warning(models_error or "Nenhum modelo encontrado")
            model_input = st.text_input(
                "Modelo (manual)",
                value="llama3",
                help="Digite o nome do modelo manualmente"
            )
        
        host_input = st.text_input(
            "Host (opcional)",
            value=os.environ.get("OLLAMA_HOST", ""),
            help="Ex.: http://localhost:11434. Deixe vazio para padrão."
        )
        
        st.caption("💡 Execute `ollama serve` e `ollama pull <modelo>` antes de usar.")
        
        st.divider()
        
        # --- VRP: Configuração de Veículos ---
        st.subheader("🚛 Frota")
        num_vehicles = st.number_input(
            "Número de veículos",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            help="Quantidade de veículos disponíveis para as rotas"
        )

    # =========================================================================
    # MAIN: Inputs de Config e Dados
    # =========================================================================
    col1, col2 = st.columns(2)
    
    with col1:
        config_path = st.text_input("📁 Config YAML", value="config.yaml")
    
    with col2:
        st.markdown("**📊 Dataset CSV**")
        uploaded_file = st.file_uploader(
            "Selecione o arquivo CSV de pontos de entrega",
            type=["csv"],
            help="Formato: id,nome,estado,latitude,longitude,demanda,prioridade,..."
        )
    
    # Determinar caminho do CSV
    data_path = None
    temp_file_path = None
    
    if uploaded_file is not None:
        # Salvar arquivo uploadado temporariamente
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
            content = uploaded_file.getvalue().decode("utf-8")
            tmp.write(content)
            temp_file_path = tmp.name
            data_path = temp_file_path
        st.success(f"✅ Arquivo carregado: {uploaded_file.name}")
    else:
        # Fallback para caminho padrão
        default_path = "src/data/capitais.csv"
        st.info(f"💡 Usando dataset padrão: {default_path}")
        data_path = default_path

    # =========================================================================
    # EXECUÇÃO
    # =========================================================================
    if st.button("🚀 Executar otimização", type="primary"):
        if not data_path:
            st.error("❌ Selecione um arquivo CSV ou use o padrão.")
            return
        
        with st.spinner("Rodando GA..."):
            try:
                solution, routes, convergence, cfg = run_optimizer(config_path, data_path, num_vehicles)
            except Exception as e:
                st.error(f"Erro: {e}")
                # Limpar arquivo temporário
                if temp_file_path and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                return

        st.success("✅ Otimização concluída!")

        # --- Métricas Globais ---
        gm = solution["global_metrics"]
        st.subheader("📊 Métricas globais")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Distância total (km)", f"{gm['distance_total_km']:.1f}")
        with col_m2:
            st.metric("Veículos usados", gm["vehicles_used"])
        with col_m3:
            st.metric("Melhor fitness", f"{gm['best_fitness']:.2f}")

        # --- Rotas JSON ---
        st.subheader("🚛 Rotas")
        st.json(solution["routes"], expanded=False)

        # --- Convergência ---
        st.subheader("📈 Convergência")
        png = plot_convergence_fig(convergence)
        st.image(png)

        # --- Mapa ---
        st.subheader("🗺️ Mapa")
        nodes_map_ui = {cfg.depot.node_id: cfg.depot, **load_nodes(data_path)}
        map_html = build_map_html(routes, cfg.depot, nodes_map_ui)
        st.components.v1.html(map_html, height=600)

        # --- LLM: Instruções e Navegação ---
        if solution["routes"]:
            # Criar cliente LLM
            try:
                client = LLMClient(
                    model_input or cfg.llm.get("model", "llama3"),
                    temperature=cfg.llm.get("temperature", 0.2),
                    host=host_input or cfg.llm.get("host"),
                )
            except Exception as e:
                st.error(f"Erro ao criar cliente LLM: {e}")
                client = None
            
            if client:
                # --- Instruções Operacionais ---
                st.subheader("📝 Instruções Operacionais (LLM)")
                try:
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
                    st.error(f"❌ Erro ao gerar instruções: {e}")

                # --- Instruções de Navegação Ponto-a-Ponto ---
                st.subheader("🧭 Navegação Ponto-a-Ponto (LLM)")
                try:
                    nav_instr = navigation_instructions_for_route(
                        client=client,
                        route=solution["routes"][0],
                        nodes_map=nodes_map_ui,
                        depot=cfg.depot,
                        departure_time=cfg.llm.get("departure_time", "08:00"),
                        vehicle_speed_kmh=cfg.vrp.vehicle_speed_kmh,
                    )
                    st.markdown(nav_instr)
                except Exception as e:
                    st.error(f"❌ Erro ao gerar navegação: {e}")

                # --- Log de Requests/Responses do LLM ---
                with st.expander("🔍 Log de Requisições LLM (Debug)"):
                    exchange = client.get_last_exchange()
                    if exchange["request"]:
                        st.markdown("**Última Requisição:**")
                        st.code(json.dumps(exchange["request"], indent=2, ensure_ascii=False), language="json")
                    if exchange["response"]:
                        st.markdown("**Última Resposta:**")
                        st.text_area("Response", exchange["response"], height=300)
                    
                    # Histórico completo
                    if client.request_history:
                        st.markdown("**Histórico de Requisições:**")
                        for i, entry in enumerate(client.request_history):
                            with st.expander(f"Request #{i+1} - {entry.get('timestamp', 'N/A')}"):
                                st.json(entry)
        else:
            st.info("💡 Nenhuma rota gerada para solicitar instruções ao LLM.")

        # Limpar arquivo temporário
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    st.caption("Execute: `streamlit run src/ui/app.py`")


if __name__ == "__main__":
    main()
