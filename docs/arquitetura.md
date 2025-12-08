# Arquitetura

## Componentes
- **core/distance.py**: Haversine e utilitários de rota.
- **core/vrp.py**: modelos (`Node`, `RouteMetrics`, `Solution`), parâmetros GA/VRP/pesos, divisão de rotas e cálculo de métricas/penalidades.
- **core/fitness.py**: cálculo de fitness agregando penalidades.
- **core/selection.py**: seleção tournament/roulette.
- **core/crossover.py**: PMX e OX.
- **core/mutation.py**: swap/inversion.
- **core/heuristics.py**: Nearest Neighbor (seed) e placeholder SA.
- **core/ga.py**: loop principal do GA com elitismo e parada por estagnação.
- **io/config.py**: loader YAML para dataclasses.
- **io/load_data.py**: leitura/validação de dataset.
- **io/output_saver.py**: salvamento JSON/MD/CSV log.
- **viz/map.py**: mapa Folium por rota.
- **viz/charts.py**: curva de convergência.
- **llm/prompts.py** e **llm/render.py**: templates e cliente OpenAI com guardrail (stub sem chave).
- **cli.py**: orquestra pipeline CLI.

## Fluxo
1. Carrega config e dataset.
2. Valida nós e monta seeds heurísticos.
3. GA: seleção → crossover → mutação → fitness → elitismo; registra convergência.
4. Reconstrói melhor indivíduo, calcula métricas globais, salva artefatos (JSON, mapa, gráfico, log JSONL, relatório MD).
5. (Opcional) Chama LLM para instruções/relatório.

## Decisões
- Penalidades simples e parametrizadas para capacidade, autonomia, prioridade e janelas.
- Divisão de rotas gulosa por capacidade; penalidades ajudam GA a ajustar permutações.
- Seeds via Nearest Neighbor para acelerar convergência.
- LLM desacoplado; sem chave devolve stub evitando falhas.

## Extensões futuras
- Inserção de OR-Tools como baseline opcional.
- Janela de tempo com cálculo de chegada cumulativa por rota.
- Balanceamento explícito (desvio padrão de carga/tempo) na função objetivo.
- Simulated Annealing real para baseline adicional.
