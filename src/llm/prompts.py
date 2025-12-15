# =============================================================================
# SYSTEM PROMPTS - Contextos especializados por função
# =============================================================================

SYSTEM_PROMPT_INSTRUCTIONS = """Você é um coordenador de frotas de logística hospitalar.
Sua função é gerar roteiros operacionais claros e objetivos para motoristas.

REGRAS OBRIGATÓRIAS:
- Use APENAS os dados fornecidos, nunca invente informações
- Linguagem direta e objetiva, sem rodeios
- Horários no formato HH:MM
- Prioridades: 1=CRÍTICO (medicamentos urgentes), 2=ALTA, 3=NORMAL
- Sempre alerte sobre entregas críticas e janelas de tempo apertadas
- Formato de saída: Markdown estruturado conforme modelo fornecido
"""

SYSTEM_PROMPT_REPORT = """Você é um analista sênior de logística hospitalar.
Sua função é produzir relatórios gerenciais com análises objetivas e recomendações acionáveis.

REGRAS OBRIGATÓRIAS:
- Use APENAS os dados fornecidos, nunca invente métricas
- Calcule percentuais de melhoria quando houver baseline
- Identifique violações de restrições (capacidade, autonomia, janelas de tempo)
- Recomendações devem ser específicas e implementáveis
- Formato de saída: Markdown com seções, tabelas e bullets
- Números com 2 casas decimais, exceto inteiros
"""

SYSTEM_PROMPT_QA = """Você é um assistente de operações logísticas hospitalares.
Responda perguntas sobre rotas e entregas de forma clara e objetiva.

REGRAS:
- Use APENAS os dados fornecidos
- Se não souber a resposta com base nos dados, diga claramente
- Justifique suas respostas com dados específicos
"""

# =============================================================================
# TEMPLATES DE INSTRUÇÕES PARA MOTORISTAS
# =============================================================================

INSTRUCTION_TEMPLATE = """
## ROTEIRO DE ENTREGAS - {vehicle_id}

**Data:** {date}
**Horário de Partida:** {departure_time}
**Motorista:** {vehicle_id}

---

### DADOS DA ROTA

| Métrica | Valor |
|---------|-------|
| Distância Total | {distance_km:.1f} km |
| Tempo Estimado | {time_min:.0f} min |
| Carga Total | {load:.1f} kg |
| Entregas | {num_stops} paradas |

---

### SEQUÊNCIA DE PARADAS

{stops_detail}

---

### ⚠️ ALERTAS E OBSERVAÇÕES

{alerts}

---

### ✅ CHECKLIST DE PARTIDA

- [ ] Verificar carga total: {load:.1f} kg
- [ ] Conferir documentação de todas as entregas
- [ ] Verificar combustível/autonomia para {distance_km:.1f} km
- [ ] Confirmar entregas CRÍTICAS primeiro
- [ ] GPS/celular carregado

---

Gere as instruções detalhadas para o motorista seguindo EXATAMENTE este formato.
Preencha {stops_detail} com a lista de paradas no formato:

**Parada N - [NOME DO LOCAL]**
- 🕐 ETA: HH:MM
- 📍 Cidade/Estado
- 📦 Carga: X kg
- ⚡ Prioridade: CRÍTICO/ALTA/NORMAL
- ⏱️ Tempo de atendimento: X min
- 📝 Observações: (janela de tempo se houver)

Dados da rota:
```json
{route_json}
```
"""

# =============================================================================
# TEMPLATE DE RELATÓRIO EXECUTIVO
# =============================================================================

REPORT_TEMPLATE = """
# RELATÓRIO DE OTIMIZAÇÃO DE ROTAS

**Data de Geração:** {date}
**Período:** {period}

---

## 1. RESUMO EXECUTIVO

Analise os dados e produza um parágrafo resumindo:
- Total de entregas realizadas
- Número de veículos utilizados
- Distância total percorrida
- Se a solução é viável (sem violações) ou possui restrições não atendidas

---

## 2. KPIs PRINCIPAIS

Preencha a tabela com os dados fornecidos:

| Indicador | Valor | Variação vs Baseline |
|-----------|-------|---------------------|
| Distância Total (km) | {distance_total:.2f} | {distance_var} |
| Tempo Total (min) | {time_total:.0f} | {time_var} |
| Veículos Utilizados | {vehicles_used} | {vehicles_var} |
| Carga Média (kg) | {load_mean:.2f} | - |
| Desvio Padrão Carga | {load_std:.2f} | - |
| Fitness Final | {best_fitness:.2f} | {fitness_var} |

---

## 3. ANÁLISE DE VIOLAÇÕES

Liste todas as penalidades encontradas nas rotas:

{violations_analysis}

---

## 4. DETALHAMENTO POR VEÍCULO

{routes_detail}

---

## 5. ANÁLISE DE CONVERGÊNCIA

O algoritmo executou {generations} gerações.
- Fitness inicial: {initial_fitness:.2f}
- Fitness final: {final_fitness:.2f}
- Melhoria: {improvement:.1f}%
- Parou por: {stop_reason}

---

## 6. RECOMENDAÇÕES

Com base na análise, liste 3-5 recomendações específicas:

1. **[Categoria]**: Descrição da recomendação
2. **[Categoria]**: Descrição da recomendação
...

Categorias sugeridas: Capacidade, Autonomia, Balanceamento, Priorização, Parâmetros do AG

---

## DADOS BRUTOS

### Solução Otimizada:
```json
{solution_json}
```

### Baseline (se disponível):
```json
{baseline_json}
```
"""

# =============================================================================
# TEMPLATE PARA Q&A
# =============================================================================

QA_TEMPLATE = """Com base nos dados da solução de rotas abaixo, responda à pergunta do usuário.

**Pergunta:** {question}

**Dados da Solução:**
```json
{solution_json}
```

Responda de forma clara e objetiva, citando os dados específicos que sustentam sua resposta."""
