# QUICK_REFERENCE.md - Cartão de Referência Rápida

**Cacheiro VRP GA** - Guia de bolso

---

## ⚡ Instalação (2 minutos)

```bash
# 1. Clone
git clone https://github.com/DanielPitthan/Projeto-Tech-Chalange-2-IA-para-DEVS.git
cd Projeto-Tech-Chalange-2-IA-para-DEVS

# 2. Instale
pip install -r requeriments.txt

# 3. Execute (escolha uma)
streamlit run src/ui/app.py          # Interface web
python -m src.cli --config config.yaml --data src/data/capitais.csv  # Linha de comando
```

---

## 🎯 Uso Rápido

### Streamlit (Interface Web)
```bash
streamlit run src/ui/app.py
# Abre em http://localhost:8501
```

**Na UI (Ollama):**
1. Rode `ollama serve`
2. Faça `ollama pull <modelo>` (ex.: llama3, qwen2.5, deepseek-r1)
3. Informe config.yaml e CSV
4. Clique "🚀 Executar otimização"
5. Veja métricas, mapa, gráficos e instruções do LLM

### CLI (Linha de Comando)
```bash
python -m src.cli --config config.yaml --data src/data/capitais.csv
# Salva em outputs/
```

---

## 📋 Configuração (config.yaml)

### GA Essenciais
```yaml
ga:
  population_size: 150          # Mais = melhor mas lento
  generations: 200              # Mais = convergência melhor
  mutation_rate: 0.2            # 0.1-0.3 recomendado
  elitism: 5                    # Preserva melhores
```

### VRP Essenciais
```yaml
vrp:
  vehicles: 5                   # Número de caminhões
  vehicle_capacity: 80          # Carga máxima
  vehicle_range_km: 1200        # Autonomia em km
```

### Pesos (ajustar se não respeita restrição X)
```yaml
weights:
  w_distance: 1.0               # Objetivo principal
  w_capacity: 60.0              # ↑ se capacidade estourando
  w_range: 60.0                 # ↑ se autonomia insuficiente
  w_priority: 25.0              # ↑ se prioridades ignoradas
  w_time: 20.0                  # ↑ se janela extrapolada
```

### LLM (Ollama local)
```yaml
llm:
  model: llama3                # ex.: llama3, llama3.2:3b-instruct, qwen2.5
  host: http://localhost:11434  # opcional; deixe vazio/ausente para padrão do Ollama
  temperature: 0.2
```

---

## 📊 Entrada (CSV)

```csv
id,nome,estado,latitude,longitude,demanda,prioridade,janela_inicio,janela_fim,tempo_atendimento_min
1,São Paulo,SP,-23.5505,-46.6333,10,1,08:00,20:00,10
2,Rio de Janeiro,RJ,-22.9068,-43.1729,15,2,08:00,20:00,15
```

**Colunas:**
- `demanda`: quantidade a entregar
- `prioridade`: 1=crítica, 2=alta, 3=normal
- `tempo_atendimento_min`: minutos gastos na parada

---

## 📤 Saída (outputs/)

| Arquivo | O quê |
|---------|-------|
| `solution.json` | Rotas em JSON (máquina) |
| `map.html` | Mapa interativo (browser) |
| `convergence.png` | Gráfico da evolução |
| `report.md` | Relatório Markdown (humano) |
| `run_log.jsonl` | Log por geração |

---

## 🔧 Troubleshooting (Top 5)

| Problema | Solução |
|----------|---------|
| "ModuleNotFoundError" | `pip install -r requeriments.txt` |
| "FileNotFoundError config.yaml" | Confira caminho em config_path |
| "Mapa vazio" | Valide CSV (lat/lon numéricos) |
| "Fitness não melhora" | Aumente `population_size`, `generations`, reduza `mutation_rate` |
| "LLM desabilitado" | Instale `pip install ollama`, rode `ollama serve` e faça `ollama pull <modelo>` |

---

## 🧬 Algoritmo Genético em 30 segundos

```
Geração 0: População aleatória (150 indivíduos)
           ↓ Avalia cada um
Geração 1: Melhor 5 passam (elitismo)
           + 145 novos via seleção + crossover + mutação
           ↓ Avalia cada um
...
Geração N: Se não melhora por 30 gerações → PARA
           ↓ Retorna melhor solução
```

**Operadores:**
- **Seleção:** Tournament (k=5)
- **Crossover:** PMX (Partially Mapped Crossover)
- **Mutação:** Inversion (inverte segmento)

---

## 🤖 IA Generativa em 30 segundos

```
GA produz rotas
    ↓
Prompt template + JSON rota
    ↓
LLMClient.complete() → Ollama local
    ↓
Instruções operacionais
```

**Modelo:**
- Ollama local (sem API key); use `ollama pull <modelo>` antes

---

## 🚀 Dev Quick Commands

```bash
# Formato código
black src/ tests/

# Lint
flake8 src/ tests/ --max-line-length=100

# Testes
pytest tests/ -v

# Cobertura
pytest tests/ --cov=src --cov-report=html

# Type check
mypy src/ --ignore-missing-imports

# Clean
rm -rf outputs/ .pytest_cache __pycache__
```

---

## 📚 Documentação Completa

| Documento | Tempo | Assunto |
|-----------|-------|---------|
| README.md | 15min | Overview, uso, config, troubleshooting |
| GUIA_TECNICO_APROFUNDADO.md | 45min | Código, arquitetura, implementação |
| CONTRIBUTING.md | 10min | Como contribuir, roadmap |
| docs/arquitetura.md | 5min | Visão geral componentes |

---

## 🌟 Dicas Pro

### 1. Convergência Rápida
```yaml
# Pequeno dataset (5-15 nós)?
population_size: 100
generations: 100

# Grande dataset (27+ nós)?
population_size: 200
generations: 300
```

### 2. Melhorar Qualidade
```yaml
# Aumentar busca exploratória:
mutation_rate: 0.3
tournament_k: 3  # Menos pressão

# Aumentar exploração:
mutation_rate: 0.1
tournament_k: 7  # Mais pressão
```

### 3. Debug Eficiente
```bash
# Teste rápido
python -c "from src.core.ga import *; print('OK')"

# Teste GA diretamente
python -m pytest tests/test_operators.py::test_pmx -v

# Veja logs
tail -f outputs/run_log.jsonl
```

---

## 📞 Quando Consultar O Quê

| Quando... | Consulte... |
|-----------|-------------|
| Não sabe instalar | README → "Como Executar" |
| Config.yaml confuso | README → "Configuração" |
| GA não converge | QUICK_REFERENCE → "Dev Quick Commands" + README → "Troubleshooting" |
| Quer contribuir | CONTRIBUTING.md |
| Quer entender GA | README → "Algoritmo Genético" |
| Quer código detalhado | GUIA_TECNICO_APROFUNDADO.md |
| Tem dúvida geral | README → Índice de Busca |

---

## ✅ Checklist de Execução

- [ ] Python 3.10+ instalado
- [ ] Dependências instaladas: `pip install -r requeriments.txt`
- [ ] config.yaml exists
- [ ] src/data/capitais.csv (ou seu CSV) exists
- [ ] Rodou `streamlit run src/ui/app.py` ou `python -m src.cli ...`
- [ ] Viu outputs em `outputs/`
- [ ] Validou JSON/mapa/gráficos

---

## 🎯 Próximos Passos

1. **Teste rápido:** `python -m src.cli --config config.yaml --data src/data/capitais.csv`
2. **Interface:** `streamlit run src/ui/app.py`
3. **Customize:** Edite `config.yaml` com seus parâmetros
4. **Contribua:** Leia CONTRIBUTING.md

---

## 📖 Estrutura de Arquivo

```
├── src/
│   ├── core/ga.py              ← Algoritmo aqui!
│   ├── io/config.py            ← Config carregada aqui
│   ├── llm/render.py           ← IA generativa aqui
│   └── ui/app.py               ← Interface Streamlit
├── config.yaml                 ← EDITE AQUI
├── src/data/capitais.csv       ← Seus dados
└── outputs/
    ├── solution.json           ← Resultado
    ├── map.html                ← Mapa
    └── convergence.png         ← Gráfico
```

---

## 🆘 SOS - Preciso Ajuda!

1. **Leia:** README.md (15 min)
2. **Pesquise:** Índice de Busca em README.md (Ctrl+F)
3. **Teste:** `pytest -q` (valida código)
4. **Debug:** Veja outputs/ e logs
5. **Pergunte:** Abra Issue no GitHub

---

**Última atualização:** Dezembro 2024  
**Versão:** 1.0  
**Acesso rápido:** Esta é uma folha de referência. Para documentação completa, veja README.md
