from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    from ollama import Client
except Exception:  # pragma: no cover
    Client = None  # type: ignore

from . import prompts


class LLMClient:
    """Cliente LLM exclusivo para Ollama local com logging de requests/responses."""

    def __init__(self, model: str, temperature: float = 0.2, host: Optional[str] = None) -> None:
        self.model = model
        self.temperature = temperature
        self.host = host
        self.client: Optional[Client] = None
        self.available = False
        
        # Logging de requests e responses
        self.last_request: Optional[Dict[str, Any]] = None
        self.last_response: Optional[str] = None
        self.request_history: List[Dict[str, Any]] = []

        if Client is not None:
            # host opcional permite apontar para outra instância; default usa localhost:11434
            self.client = Client(host=host) if host else Client()
            self.available = True

    def complete(self, system: str, user: str) -> str:
        # Armazena request para logging
        self.last_request = {
            "model": self.model,
            "system": system[:500] + "..." if len(system) > 500 else system,
            "user": user[:1000] + "..." if len(user) > 1000 else user,
            "temperature": self.temperature,
            "timestamp": datetime.now().isoformat(),
        }
        
        if not self.available or self.client is None:
            self.last_response = "[LLM desabilitado: instale o pacote 'ollama' (pip install ollama) e execute 'ollama serve']"
            self._save_to_history()
            return self.last_response

        try:
            resp = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                options={"temperature": self.temperature},
            )
        except Exception as e:  # pragma: no cover - retorno de erro ao usuário final
            self.last_response = f"[Erro ao chamar Ollama: {e}]"
            self._save_to_history()
            return self.last_response

        # resp.message.content já contém o texto final; manter fallback seguro
        try:
            self.last_response = resp.message.content or ""
        except Exception:
            self.last_response = ""
        
        self._save_to_history()
        return self.last_response
    
    def _save_to_history(self) -> None:
        """Salva request/response no histórico."""
        if self.last_request:
            entry = {
                **self.last_request,
                "response": self.last_response[:2000] + "..." if self.last_response and len(self.last_response) > 2000 else self.last_response,
            }
            self.request_history.append(entry)
            # Manter apenas últimos 10 requests
            if len(self.request_history) > 10:
                self.request_history = self.request_history[-10:]
    
    def get_last_exchange(self) -> Dict[str, Any]:
        """Retorna último request e response para exibição."""
        return {
            "request": self.last_request,
            "response": self.last_response,
        }


# =============================================================================
# FUNÇÕES DE ENRIQUECIMENTO DE DADOS
# =============================================================================

def _parse_time(time_str: str) -> datetime:
    """Converte string HH:MM para datetime."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    parts = time_str.split(":")
    return today.replace(hour=int(parts[0]), minute=int(parts[1]))


def _format_time(dt: datetime) -> str:
    """Formata datetime para HH:MM."""
    return dt.strftime("%H:%M")


def _priority_label(priority: int) -> str:
    """Converte prioridade numérica para label."""
    labels = {1: "CRITICO", 2: "ALTA", 3: "NORMAL"}
    return labels.get(priority, "NORMAL")


def enrich_route_for_llm(
    route: Dict[str, Any],
    nodes_map: Dict[int, Any],
    depot: Any,
    departure_time: str = "08:00",
    vehicle_speed_kmh: float = 60.0,
) -> Dict[str, Any]:
    """
    Enriquece uma rota com nomes, ETAs acumulativos e detalhes de cada parada.
    
    Args:
        route: Dict com sequence, distance_km, time_min, load, penalties
        nodes_map: Mapeamento id -> Node com name, lat, lon, demand, priority, etc.
        depot: Node do depósito
        departure_time: Horário de partida (HH:MM)
        vehicle_speed_kmh: Velocidade média para cálculo de ETA
    
    Returns:
        Dict enriquecido com stops_detail, alerts, e todos os campos necessários
    """
    sequence = route.get("sequence", [])
    current_time = _parse_time(departure_time)
    
    stops = []
    alerts = []
    critical_count = 0
    
    # Processar cada parada na sequência
    for i, node_id in enumerate(sequence):
        # Pular depósito de origem
        if i == 0:
            continue
        
        # Pular depósito de retorno (último da sequência)
        if i == len(sequence) - 1 and node_id == depot.node_id:
            continue
        
        # Obter dados do nó
        node = nodes_map.get(node_id)
        if node is None:
            continue
        
        # Se for o depósito no meio da rota, pular
        if node_id == depot.node_id:
            continue
        
        # Calcular tempo de deslocamento desde a parada anterior
        prev_node_id = sequence[i - 1]
        prev_node = nodes_map.get(prev_node_id, depot)
        
        # Usar distância aproximada (haversine seria melhor, mas usamos estimativa)
        # O tempo já está calculado na rota, distribuímos proporcionalmente
        travel_time_min = route.get("time_min", 0) / max(len(sequence) - 2, 1)
        
        # Atualizar horário atual
        current_time += timedelta(minutes=travel_time_min)
        eta = _format_time(current_time)
        
        # Verificar janela de tempo
        time_window = ""
        window_alert = ""
        if hasattr(node, "window_start") and hasattr(node, "window_end"):
            if node.window_start and node.window_end:
                time_window = f"{node.window_start} - {node.window_end}"
                # Verificar se ETA está dentro da janela
                window_end = _parse_time(node.window_end)
                if current_time > window_end:
                    delay_min = (current_time - window_end).total_seconds() / 60
                    window_alert = f"⚠️ ATRASO: {delay_min:.0f} min após janela"
                    alerts.append(f"Parada {len(stops)+1} ({node.name}): {window_alert}")
        
        # Verificar prioridade crítica
        priority = getattr(node, "priority", 3)
        if priority == 1:
            critical_count += 1
            if len(stops) > 2:  # Se crítico não está nas primeiras paradas
                alerts.append(f"⚡ ATENÇÃO: Entrega CRÍTICA em {node.name} - verificar se pode antecipar")
        
        stop = {
            "order": len(stops) + 1,
            "node_id": node_id,
            "name": getattr(node, "name", f"Ponto {node_id}"),
            "city_state": getattr(node, "state", ""),
            "lat": getattr(node, "lat", 0),
            "lon": getattr(node, "lon", 0),
            "eta": eta,
            "demand": getattr(node, "demand", 0),
            "priority": priority,
            "priority_label": _priority_label(priority),
            "service_time_min": getattr(node, "service_time_min", 10),
            "time_window": time_window,
            "window_alert": window_alert,
        }
        stops.append(stop)
        
        # Adicionar tempo de atendimento
        current_time += timedelta(minutes=stop["service_time_min"])
    
    # Verificar penalidades e gerar alertas
    penalties = route.get("penalties", {})
    if penalties.get("capacity", 0) > 0:
        alerts.append(f"⚠️ CAPACIDADE EXCEDIDA: veículo sobrecarregado")
    if penalties.get("range", 0) > 0:
        alerts.append(f"⚠️ AUTONOMIA: rota excede autonomia do veículo - verificar abastecimento")
    if penalties.get("time", 0) > 0:
        alerts.append(f"⚠️ TEMPO: rota excede janela de trabalho")
    
    # Formatar detalhes das paradas para o template
    stops_detail_lines = []
    for stop in stops:
        lines = [
            f"**Parada {stop['order']} - {stop['name']}**",
            f"- ETA: {stop['eta']}",
            f"- Cidade: {stop['city_state']}" if stop['city_state'] else "",
            f"- Carga: {stop['demand']:.1f} kg",
            f"- Prioridade: {stop['priority_label']}",
            f"- Tempo de atendimento: {stop['service_time_min']} min",
        ]
        if stop['time_window']:
            lines.append(f"- Janela: {stop['time_window']}")
        if stop['window_alert']:
            lines.append(f"- {stop['window_alert']}")
        lines.append("")  # Linha em branco entre paradas
        stops_detail_lines.extend([l for l in lines if l])  # Remove linhas vazias no meio
        stops_detail_lines.append("")
    
    stops_detail = "\n".join(stops_detail_lines)
    
    # Formatar alertas
    if not alerts:
        alerts_text = "NENHUM: Rota dentro dos parametros."
    else:
        alerts_text = "\n".join([f"- {a}" for a in alerts])
    
    return {
        "vehicle_id": route.get("vehicle_id", "V1"),
        "date": datetime.now().strftime("%d/%m/%Y"),
        "departure_time": departure_time,
        "distance_km": route.get("distance_km", 0),
        "time_min": route.get("time_min", 0),
        "load": route.get("load", 0),
        "num_stops": len(stops),
        "stops": stops,
        "stops_detail": stops_detail,
        "alerts": alerts_text,
        "penalties": penalties,
        "critical_count": critical_count,
        "route_json": json.dumps(route, indent=2, ensure_ascii=False),
    }


def enrich_solution_for_report(
    solution_json: Dict[str, Any],
    nodes_map: Dict[int, Any],
    depot: Any,
    baseline_json: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Enriquece a solução completa para geração de relatório.
    
    Args:
        solution_json: JSON da solução com routes, global_metrics, convergence
        nodes_map: Mapeamento id -> Node
        depot: Node do depósito
        baseline_json: JSON do baseline para comparação (opcional)
    
    Returns:
        Dict com todos os campos necessários para o REPORT_TEMPLATE
    """
    global_metrics = solution_json.get("global_metrics", {})
    routes = solution_json.get("routes", [])
    convergence = solution_json.get("convergence", [])
    
    # Calcular variações vs baseline
    def calc_var(current: float, baseline: float) -> str:
        if baseline == 0:
            return "-"
        var = ((current - baseline) / baseline) * 100
        sign = "+" if var > 0 else ""
        return f"{sign}{var:.1f}%"
    
    baseline_metrics = {}
    if baseline_json:
        baseline_metrics = baseline_json.get("global_metrics", {})
    
    distance_total = global_metrics.get("distance_total_km", 0)
    time_total = sum(r.get("time_min", 0) for r in routes)
    vehicles_used = global_metrics.get("vehicles_used", 0)
    
    # Variações
    distance_var = calc_var(distance_total, baseline_metrics.get("distance_total_km", 0)) if baseline_metrics else "-"
    time_var = "-"  # Baseline pode não ter tempo total
    vehicles_var = calc_var(vehicles_used, baseline_metrics.get("vehicles_used", 0)) if baseline_metrics else "-"
    fitness_var = calc_var(global_metrics.get("best_fitness", 0), baseline_metrics.get("best_fitness", 0)) if baseline_metrics else "-"
    
    # Análise de violações
    violations = []
    for r in routes:
        penalties = r.get("penalties", {})
        vid = r.get("vehicle_id", "?")
        if penalties.get("capacity", 0) > 0:
            violations.append(f"- **{vid}**: Capacidade excedida (penalidade: {penalties['capacity']:.2f})")
        if penalties.get("range", 0) > 0:
            violations.append(f"- **{vid}**: Autonomia excedida (penalidade: {penalties['range']:.2f})")
        if penalties.get("priority", 0) > 0:
            violations.append(f"- **{vid}**: Prioridades não otimizadas (penalidade: {penalties['priority']:.2f})")
        if penalties.get("time", 0) > 0:
            violations.append(f"- **{vid}**: Janela de tempo violada (penalidade: {penalties['time']:.2f})")
    
    if not violations:
        violations_analysis = "✅ **Nenhuma violação de restrições.** Solução 100% viável."
    else:
        violations_analysis = "\n".join(violations)
    
    # Detalhamento por veículo
    routes_detail_lines = []
    for r in routes:
        vid = r.get("vehicle_id", "?")
        seq = r.get("sequence", [])
        # Converter IDs para nomes
        stop_names = []
        for node_id in seq:
            if node_id == depot.node_id:
                stop_names.append("[Deposito]")
            else:
                node = nodes_map.get(node_id)
                name = getattr(node, "name", f"Ponto {node_id}") if node else f"Ponto {node_id}"
                stop_names.append(name)
        
        route_str = " -> ".join(stop_names)
        lines = [
            f"### {vid}",
            f"- **Rota:** {route_str}",
            f"- **Distancia:** {r.get('distance_km', 0):.2f} km",
            f"- **Tempo:** {r.get('time_min', 0):.0f} min",
            f"- **Carga:** {r.get('load', 0):.1f} kg",
            "",
        ]
        routes_detail_lines.extend(lines)
    
    routes_detail = "\n".join(routes_detail_lines)
    
    # Análise de convergência
    generations = len(convergence)
    initial_fitness = convergence[0].get("best_fitness", 0) if convergence else 0
    final_fitness = convergence[-1].get("best_fitness", 0) if convergence else 0
    improvement = ((initial_fitness - final_fitness) / initial_fitness * 100) if initial_fitness > 0 else 0
    
    # Determinar razão de parada
    if generations >= 300:  # Assumindo 300 como máximo do config
        stop_reason = "Máximo de gerações atingido"
    else:
        stop_reason = "Convergência por estagnação"
    
    return {
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "period": "Diário",
        "distance_total": distance_total,
        "time_total": time_total,
        "vehicles_used": vehicles_used,
        "load_mean": global_metrics.get("load_mean", 0),
        "load_std": global_metrics.get("load_std", 0),
        "best_fitness": global_metrics.get("best_fitness", 0),
        "distance_var": distance_var,
        "time_var": time_var,
        "vehicles_var": vehicles_var,
        "fitness_var": fitness_var,
        "violations_analysis": violations_analysis,
        "routes_detail": routes_detail,
        "generations": generations,
        "initial_fitness": initial_fitness,
        "final_fitness": final_fitness,
        "improvement": improvement,
        "stop_reason": stop_reason,
        "solution_json": json.dumps(solution_json, indent=2, ensure_ascii=False),
        "baseline_json": json.dumps(baseline_json, indent=2, ensure_ascii=False) if baseline_json else "null",
    }


# =============================================================================
# FUNÇÕES DE GERAÇÃO COM LLM
# =============================================================================

def instructions_for_route(
    client: LLMClient,
    route: Dict[str, Any],
    nodes_map: Dict[int, Any],
    depot: Any,
    departure_time: str = "08:00",
    vehicle_speed_kmh: float = 60.0,
) -> str:
    """
    Gera instruções detalhadas para um motorista.
    
    Args:
        client: Cliente LLM configurado
        route: Dict da rota (sequence, distance_km, etc.)
        nodes_map: Mapeamento id -> Node
        depot: Node do depósito
        departure_time: Horário de partida (HH:MM)
        vehicle_speed_kmh: Velocidade média do veículo
    
    Returns:
        String com instruções formatadas em Markdown
    """
    # Enriquecer dados da rota
    enriched = enrich_route_for_llm(
        route=route,
        nodes_map=nodes_map,
        depot=depot,
        departure_time=departure_time,
        vehicle_speed_kmh=vehicle_speed_kmh,
    )
    
    # Tentar usar LLM, se disponível
    if client.available:
        user_prompt = prompts.INSTRUCTION_TEMPLATE.format(**enriched)
        llm_response = client.complete(prompts.SYSTEM_PROMPT_INSTRUCTIONS, user_prompt)
        if not llm_response.startswith("[LLM") and not llm_response.startswith("[Erro"):
            return llm_response
    
    # Fallback: gerar instruções estruturadas sem LLM
    return _generate_instructions_fallback(enriched)


def _generate_instructions_fallback(enriched: Dict[str, Any]) -> str:
    """Gera instruções formatadas sem usar LLM."""
    lines = [
        f"## ROTEIRO DE ENTREGAS - {enriched['vehicle_id']}",
        "",
        f"**Data:** {enriched['date']}",
        f"**Horario de Partida:** {enriched['departure_time']}",
        "",
        "---",
        "",
        "### DADOS DA ROTA",
        "",
        "| Metrica | Valor |",
        "|---------|-------|",
        f"| Distancia Total | {enriched['distance_km']:.1f} km |",
        f"| Tempo Estimado | {enriched['time_min']:.0f} min |",
        f"| Carga Total | {enriched['load']:.1f} kg |",
        f"| Entregas | {enriched['num_stops']} paradas |",
        "",
        "---",
        "",
        "### SEQUENCIA DE PARADAS",
        "",
        enriched['stops_detail'],
        "",
        "---",
        "",
        "### ALERTAS E OBSERVACOES",
        "",
        enriched['alerts'],
        "",
        "---",
        "",
        "### CHECKLIST DE PARTIDA",
        "",
        f"- [ ] Verificar carga total: {enriched['load']:.1f} kg",
        "- [ ] Conferir documentacao de todas as entregas",
        f"- [ ] Verificar combustivel/autonomia para {enriched['distance_km']:.1f} km",
        "- [ ] Confirmar entregas CRITICAS primeiro",
        "- [ ] GPS/celular carregado",
        "",
    ]
    return "\n".join(lines)


def executive_report(
    client: LLMClient,
    solution_json: Dict[str, Any],
    nodes_map: Dict[int, Any],
    depot: Any,
    baseline_json: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Gera relatório executivo da otimização.
    
    Args:
        client: Cliente LLM configurado
        solution_json: JSON da solução completa
        nodes_map: Mapeamento id -> Node
        depot: Node do depósito
        baseline_json: JSON do baseline para comparação (opcional)
    
    Returns:
        String com relatório formatado em Markdown
    """
    # Enriquecer dados para relatório
    enriched = enrich_solution_for_report(
        solution_json=solution_json,
        nodes_map=nodes_map,
        depot=depot,
        baseline_json=baseline_json,
    )
    
    # Tentar usar LLM, se disponível
    if client.available:
        user_prompt = prompts.REPORT_TEMPLATE.format(**enriched)
        llm_response = client.complete(prompts.SYSTEM_PROMPT_REPORT, user_prompt)
        if not llm_response.startswith("[LLM") and not llm_response.startswith("[Erro"):
            return llm_response
    
    # Fallback: gerar relatório estruturado sem LLM
    return _generate_report_fallback(enriched)


def _generate_report_fallback(enriched: Dict[str, Any]) -> str:
    """Gera relatório formatado sem usar LLM."""
    lines = [
        "# RELATORIO DE OTIMIZACAO DE ROTAS",
        "",
        f"**Data de Geracao:** {enriched['date']}",
        f"**Periodo:** {enriched['period']}",
        "",
        "---",
        "",
        "## 1. RESUMO EXECUTIVO",
        "",
        f"Esta otimizacao utilizou **{enriched['vehicles_used']} veiculos** para realizar as entregas, ",
        f"percorrendo um total de **{enriched['distance_total']:.2f} km** em aproximadamente ",
        f"**{enriched['time_total']:.0f} minutos**.",
        "",
        "---",
        "",
        "## 2. KPIs PRINCIPAIS",
        "",
        "| Indicador | Valor | Variacao vs Baseline |",
        "|-----------|-------|---------------------|",
        f"| Distancia Total (km) | {enriched['distance_total']:.2f} | {enriched['distance_var']} |",
        f"| Tempo Total (min) | {enriched['time_total']:.0f} | {enriched['time_var']} |",
        f"| Veiculos Utilizados | {enriched['vehicles_used']} | {enriched['vehicles_var']} |",
        f"| Carga Media (kg) | {enriched['load_mean']:.2f} | - |",
        f"| Desvio Padrao Carga | {enriched['load_std']:.2f} | - |",
        f"| Fitness Final | {enriched['best_fitness']:.2f} | {enriched['fitness_var']} |",
        "",
        "---",
        "",
        "## 3. ANALISE DE VIOLACOES",
        "",
        enriched['violations_analysis'],
        "",
        "---",
        "",
        "## 4. DETALHAMENTO POR VEICULO",
        "",
        enriched['routes_detail'],
        "",
        "---",
        "",
        "## 5. ANALISE DE CONVERGENCIA",
        "",
        f"O algoritmo executou **{enriched['generations']} geracoes**.",
        "",
        f"- **Fitness inicial:** {enriched['initial_fitness']:.2f}",
        f"- **Fitness final:** {enriched['final_fitness']:.2f}",
        f"- **Melhoria:** {enriched['improvement']:.1f}%",
        f"- **Parou por:** {enriched['stop_reason']}",
        "",
        "---",
        "",
        "## 6. RECOMENDACOES",
        "",
        "Com base na analise dos dados:",
        "",
        "1. **Autonomia:** Todas as rotas excedem a autonomia configurada. Considere aumentar o parametro `vehicle_range_km` ou adicionar mais veiculos.",
        "",
        "2. **Balanceamento:** O desvio padrao de carga indica desbalanceamento entre veiculos. Ajuste os pesos da funcao fitness.",
        "",
        "3. **Parametros AG:** Se a convergencia estagnou cedo, aumente `mutation_rate` ou `stagnation_patience`.",
        "",
    ]
    return "\n".join(lines)


def answer_question(
    client: LLMClient,
    solution_json: Dict[str, Any],
    question: str,
) -> str:
    """
    Responde perguntas sobre a solução.
    
    Args:
        client: Cliente LLM configurado
        solution_json: JSON da solução
        question: Pergunta do usuário
    
    Returns:
        String com resposta
    """
    user_prompt = prompts.QA_TEMPLATE.format(
        question=question,
        solution_json=json.dumps(solution_json, indent=2, ensure_ascii=False),
    )
    return client.complete(prompts.SYSTEM_PROMPT_QA, user_prompt)


def generate_all_instructions(
    client: LLMClient,
    solution_json: Dict[str, Any],
    nodes_map: Dict[int, Any],
    depot: Any,
    departure_time: str = "08:00",
    vehicle_speed_kmh: float = 60.0,
) -> str:
    """
    Gera instruções para todos os motoristas em um único documento.
    
    Args:
        client: Cliente LLM configurado
        solution_json: JSON da solução completa
        nodes_map: Mapeamento id -> Node
        depot: Node do depósito
        departure_time: Horário de partida
        vehicle_speed_kmh: Velocidade média
    
    Returns:
        String com todas as instruções consolidadas
    """
    routes = solution_json.get("routes", [])
    all_instructions = ["# INSTRUÇÕES DE ENTREGA - TODOS OS VEÍCULOS\n"]
    all_instructions.append(f"**Data:** {datetime.now().strftime('%d/%m/%Y')}\n")
    all_instructions.append(f"**Horário Base de Partida:** {departure_time}\n")
    all_instructions.append("---\n")
    
    for route in routes:
        instructions = instructions_for_route(
            client=client,
            route=route,
            nodes_map=nodes_map,
            depot=depot,
            departure_time=departure_time,
            vehicle_speed_kmh=vehicle_speed_kmh,
        )
        all_instructions.append(instructions)
        all_instructions.append("\n---\n")
    
    return "\n".join(all_instructions)


def navigation_instructions_for_route(
    client: LLMClient,
    route: Dict[str, Any],
    nodes_map: Dict[int, Any],
    depot: Any,
    departure_time: str = "08:00",
    vehicle_speed_kmh: float = 60.0,
) -> str:
    """
    Gera instruções de navegação ponto-a-ponto para um motorista.
    
    Args:
        client: Cliente LLM configurado
        route: Dict da rota (sequence, distance_km, etc.)
        nodes_map: Mapeamento id -> Node
        depot: Node do depósito
        departure_time: Horário de partida (HH:MM)
        vehicle_speed_kmh: Velocidade média do veículo
    
    Returns:
        String com instruções de navegação em Markdown
    """
    sequence = route.get("sequence", [])
    
    # Montar sequência de pontos com coordenadas
    points_lines = []
    for i, node_id in enumerate(sequence):
        node = nodes_map.get(node_id)
        if node is None:
            continue
        
        if node_id == depot.node_id:
            point_type = "[DEPÓSITO]" if i == 0 else "[RETORNO DEPÓSITO]"
            name = depot.name
        else:
            point_type = f"[PARADA {i}]"
            name = getattr(node, "name", f"Ponto {node_id}")
        
        state = getattr(node, "state", "")
        lat = getattr(node, "lat", 0)
        lon = getattr(node, "lon", 0)
        
        points_lines.append(
            f"{i+1}. {point_type} **{name}** ({state}) - Coords: ({lat:.4f}, {lon:.4f})"
        )
    
    points_sequence = "\n".join(points_lines)
    
    # Preparar dados para o template
    enriched = {
        "vehicle_id": route.get("vehicle_id", "V1"),
        "departure_time": departure_time,
        "num_stops": len([nid for nid in sequence if nid != depot.node_id]),
        "distance_km": route.get("distance_km", 0),
        "points_sequence": points_sequence,
    }
    
    # Tentar usar LLM
    if client.available:
        user_prompt = prompts.NAVIGATION_TEMPLATE.format(**enriched)
        llm_response = client.complete(prompts.SYSTEM_PROMPT_NAVIGATION, user_prompt)
        if not llm_response.startswith("[LLM") and not llm_response.startswith("[Erro"):
            return llm_response
    
    # Fallback: gerar navegação básica sem LLM
    return _generate_navigation_fallback(sequence, nodes_map, depot, departure_time, vehicle_speed_kmh)


def _generate_navigation_fallback(
    sequence: List[int],
    nodes_map: Dict[int, Any],
    depot: Any,
    departure_time: str,
    vehicle_speed_kmh: float,
) -> str:
    """Gera instruções de navegação básicas sem LLM."""
    from src.core.distance import haversine
    
    lines = [
        "# 🧭 INSTRUÇÕES DE NAVEGAÇÃO",
        "",
        f"**Horário de Partida:** {departure_time}",
        "",
        "---",
        "",
        "## ROTEIRO PONTO-A-PONTO",
        "",
    ]
    
    prev_node = depot
    for i, node_id in enumerate(sequence):
        if i == 0:
            continue  # Pular depósito inicial
        
        node = nodes_map.get(node_id)
        if node is None:
            continue
        
        # Calcular distância do trecho
        try:
            dist = haversine(prev_node.lat, prev_node.lon, node.lat, node.lon)
        except Exception:
            dist = 0
        
        time_min = (dist / vehicle_speed_kmh) * 60 if vehicle_speed_kmh > 0 else 0
        
        # Determinar direção geral
        lat_diff = node.lat - prev_node.lat
        lon_diff = node.lon - prev_node.lon
        
        directions = []
        if lat_diff > 0.5:
            directions.append("Norte")
        elif lat_diff < -0.5:
            directions.append("Sul")
        if lon_diff > 0.5:
            directions.append("Leste")
        elif lon_diff < -0.5:
            directions.append("Oeste")
        
        direction_str = "-".join(directions) if directions else "Proximidades"
        
        prev_name = getattr(prev_node, "name", "Ponto anterior")
        curr_name = getattr(node, "name", f"Ponto {node_id}")
        
        lines.extend([
            f"### 🚗 Trecho {i}: {prev_name} → {curr_name}",
            f"- **Distância:** ~{dist:.1f} km",
            f"- **Tempo estimado:** ~{time_min:.0f} min",
            f"- **Direção geral:** {direction_str}",
            f"- **Coordenadas destino:** ({node.lat:.4f}, {node.lon:.4f})",
            "",
        ])
        
        prev_node = node
    
    lines.extend([
        "---",
        "",
        "⚠️ **IMPORTANTE:** Estas são estimativas baseadas em distância em linha reta.",
        "Utilize GPS/Waze para navegação real.",
        "",
    ])
    
    return "\n".join(lines)
