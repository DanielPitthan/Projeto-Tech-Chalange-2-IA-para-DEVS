# CONTRIBUTING.md - Guia de Contribuição

Obrigado por se interessar em contribuir com o Cacheiro VRP GA! Este documento descreve como você pode ajudar a melhorar o projeto.

## Índice

1. [Código de Conduta](#código-de-conduta)
2. [Como Começar](#como-começar)
3. [Encontrando Issues](#encontrando-issues)
4. [Processo de Desenvolvimento](#processo-de-desenvolvimento)
5. [Padrões de Código](#padrões-de-código)
6. [Testes](#testes)
7. [Pull Requests](#pull-requests)
8. [Reportando Bugs](#reportando-bugs)
9. [Sugestões de Features](#sugestões-de-features)
10. [Roadmap do Projeto](#roadmap-do-projeto)

---

## Código de Conduta

- ✅ Seja respeitoso com outros contribuidores
- ✅ Forneça feedback construtivo
- ❌ Não há tolerância para assédio, discriminação ou abuso
- ✅ Comunique-se de forma clara e profissional

---

## Como Começar

### 1. Fork o Repositório

```bash
# Clique em "Fork" no GitHub
# Depois clone seu fork localmente
git clone https://github.com/SEU_USUARIO/Projeto-Tech-Chalange-2-IA-para-DEVS.git
cd Projeto-Tech-Chalange-2-IA-para-DEVS
```

### 2. Configure o Ambiente

```bash
# Crie um virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instale dependências
pip install -r requeriments.txt
pip install pytest pylance black flake8

# Configure pre-commit hooks (opcional)
pip install pre-commit
pre-commit install
```

### 3. Crie uma Branch

```bash
# Sempre trabalhe em uma nova branch
git checkout -b feature/nome-descritivo
# ou
git checkout -b bugfix/nome-descritivo
```

**Convenção de Nomes:**
- `feature/` - Nova funcionalidade
- `bugfix/` - Correção de bug
- `docs/` - Melhorias de documentação
- `refactor/` - Reestruturação de código
- `test/` - Adicionar testes

---

## Encontrando Issues

### Issues Abertas

Veja [issues abertas](https://github.com/DanielPitthan/Projeto-Tech-Chalange-2-IA-para-DEVS/issues) e procure por:

- 🆘 **good-first-issue:** Perfeito para iniciantes
- 📚 **documentation:** Melhorias de docs
- 🐛 **bug:** Correções necessárias
- ✨ **enhancement:** Novas features

### Reclamando uma Issue

Comente na issue: "Vou trabalhar nessa! 👋"

---

## Processo de Desenvolvimento

### 1. Faça suas Mudanças

```bash
# Edite os arquivos
# Teste localmente
pytest -q
```

### 2. Commit com Mensagem Clara

```bash
# Boas mensagens de commit
git add .
git commit -m "feat: adiciona validação de horário na rota"
git commit -m "fix: corrige cálculo de autonomia em haversine"
git commit -m "docs: expande guia de configuração"
git commit -m "test: adiciona testes para função fitness"
git commit -m "refactor: extrai lógica de split_routes em função"
```

**Formato recomendado (Conventional Commits):**
```
<tipo>(<escopo>): <descrição>

<corpo opcional>

<footer opcional>
```

**Tipos:**
- `feat` - Nova feature
- `fix` - Correção de bug
- `docs` - Documentação
- `test` - Testes
- `refactor` - Refatoração
- `perf` - Performance
- `chore` - Build, deps, etc

### 3. Push para sua Fork

```bash
git push origin feature/nome-descritivo
```

---

## Padrões de Código

### Python Style Guide (PEP 8)

Usamos [Black](https://github.com/psf/black) para formatação automática:

```bash
# Formata todo o código
black src/ tests/

# Verifica linting
flake8 src/ tests/
```

### Type Hints (PEP 484)

Sempre inclua type hints:

```python
# ❌ Ruim
def evaluate_individual(perm, nodes, depot, vrp, weights):
    ...

# ✅ Bom
from typing import Dict, List, Sequence
from src.core.vrp import Node, VRPParams, WeightParams, RouteMetrics

def evaluate_individual(
    permutation: Sequence[int],
    nodes_map: Dict[int, Node],
    depot: Node,
    vrp: VRPParams,
    weights: WeightParams,
) -> tuple[float, List[RouteMetrics]]:
    ...
```

### Docstrings (Google Style)

```python
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distância entre dois pontos (Haversine).
    
    Args:
        lat1: Latitude do primeiro ponto (graus).
        lon1: Longitude do primeiro ponto (graus).
        lat2: Latitude do segundo ponto (graus).
        lon2: Longitude do segundo ponto (graus).
    
    Returns:
        Distância em quilômetros.
    
    Raises:
        ValueError: Se coordenadas fora do range [-90,90] lat ou [-180,180] lon.
    
    Example:
        >>> haversine(-23.55, -46.63, -22.90, -43.17)
        431.2
    """
    ...
```

### Limites de Linha

- ✅ Máximo 100 caracteres (configure no editor)
- ❌ Evite linhas > 120

### Nomes Significativos

```python
# ❌ Ruim
def f(x, y):
    return x + y

# ✅ Bom
def calculate_total_distance(route_sequence: List[int], nodes_map: Dict[int, Node]) -> float:
    ...
```

### Imports

```python
# 1. Stdlib
import json
import os
from pathlib import Path
from typing import Dict, List

# 2. Third-party
import pandas as pd
import yaml
import folium

# 3. Local
from src.core.vrp import Node, VRPParams
from src.io.config import ConfigLoader
```

---

## Testes

### Executar Testes

```bash
# Todos os testes
pytest -v

# Testes com cobertura
pytest --cov=src tests/

# Um arquivo específico
pytest tests/test_fitness.py -v

# Uma função específica
pytest tests/test_fitness.py::test_penalty_capacity -v
```

### Estrutura de Teste

```python
# tests/test_novo_modulo.py
import pytest
from src.core.ga import GeneticAlgorithm
from src.core.vrp import Node

class TestGeneticAlgorithm:
    """Testes para a classe GeneticAlgorithm."""
    
    @pytest.fixture
    def sample_nodes(self):
        """Fixture com nós de exemplo."""
        return {
            0: Node(node_id=0, name="Depot", state="SP", lat=-23.5, lon=-46.6, ...),
            1: Node(node_id=1, name="São Paulo", state="SP", lat=-23.55, lon=-46.63, ...),
        }
    
    def test_population_size(self, sample_nodes):
        """Verifica se população inicial tem tamanho correto."""
        ga = GeneticAlgorithm(sample_nodes, ...)
        pop = ga.initial_population(base_orders=[])
        
        assert len(pop) == ga.ga.population_size
        assert all(len(indiv) == len(sample_nodes) - 1 for indiv in pop)

    def test_crossover_valid_permutation(self):
        """Verifica se crossover produz permutações válidas."""
        parent1 = [1, 2, 3, 4, 5]
        parent2 = [5, 4, 3, 2, 1]
        
        ga = GeneticAlgorithm(...)
        child1, child2 = ga.crossover(parent1, parent2)
        
        assert len(set(child1)) == len(child1)  # Sem duplicatas
        assert set(child1) == set(parent1)      # Mesmos elementos
```

### Coverage Target

- Alvo: 80%+ de cobertura
- Crítico (GA, fitness): 100%
- Utilitários (IO, viz): 70%+

---

## Pull Requests

### Antes de Submeter

- [ ] Código formatado com `black`
- [ ] Sem erros `flake8`
- [ ] Testes passando (`pytest`)
- [ ] Cobertura > 80%
- [ ] Docstrings completas
- [ ] README atualizado (se necessário)

### Template de PR

```markdown
## Descrição

Breve descrição do que foi alterado e por quê.

## Issue Relacionada

Resolve #123

## Tipo de Mudança

- [ ] Bug fix (correção de bug)
- [ ] Feature (nova funcionalidade)
- [ ] Breaking change (altera API existente)
- [ ] Documentation (atualiza docs)

## Como Testar

1. Instale dependências
2. Execute `pytest -v`
3. Rode `streamlit run src/ui/app.py`
4. Teste com config.yaml modificado

## Checklist

- [ ] Código segue padrões do projeto
- [ ] Testes adicionados/atualizados
- [ ] Documentação atualizada
- [ ] Sem erros de linting
- [ ] Commits com mensagens claras

## Screenshots (se aplicável)

[Adicionar screenshots de UI changes]
```

### Revisão de PR

Os maintainers farão code review e sugerirão mudanças se necessário. Seja receptivo a feedback!

---

## Reportando Bugs

### Template de Issue

```markdown
## Descrição do Bug

[Descrição clara do problema]

## Passos para Reproduzir

1. Instale o projeto com `pip install -r requeriments.txt`
2. Configure `config.yaml` assim:
   [cole config relevante]
3. Execute `streamlit run src/ui/app.py`
4. [outros passos...]

## Comportamento Esperado

[O que deveria acontecer]

## Comportamento Atual

[O que realmente acontece]

## Screenshots/Logs

[Erros, tracebacks, screenshots]

## Ambiente

- Python: 3.10.x
- SO: Windows/Linux/macOS
- Streamlit: 1.28.0
- Outras dependências relevantes

## Contexto Adicional

[Qualquer informação extra]
```

---

## Sugestões de Features

### Template de Feature Request

```markdown
## Descrição

[Qual problema a feature resolve? Por que é necessária?]

## Solução Proposta

[Como você imagina a solução?]

## Alternativas Consideradas

[Outras abordagens e por que foram rejeitadas]

## Contexto Adicional

[Mockups, exemplos, referências]
```

---

## Roadmap do Projeto

### ✅ Fase 1 (Completa)
- Algoritmo Genético básico (PMX, OX, tournament, roulette)
- Função fitness com penalidades
- Carregamento de config YAML e dados CSV
- CLI básica

### 🟡 Fase 2 (Em Progresso)
- [x] Interface Streamlit
- [x] Visualização de mapa Folium
- [x] Integração LLM (OpenAI/Gemini)
- [x] Testes unitários
- [ ] Documentação aprofundada (em progresso)
- [ ] Tratamento de erros robusto

### 🔵 Fase 3 (Planejada)
- **Multi-objetivo (NSGA-II):** Otimizar distância + custo + emissões
- **Janelas de tempo reais:** Com cálculo de chegada cumulativa
- **Múltiplos depósitos:** Roteamento multi-hub
- **Veículos heterogêneos:** Capacidades diferentes
- **Integração Or-Tools:** Como baseline de comparação
- **API REST:** FastAPI + Deploy Heroku/AWS

### 🟣 Fase 4 (Longo Prazo)
- Dashboard web avançado (React)
- Persistência em banco de dados (PostgreSQL)
- Sistema de notificações (WebSocket)
- Suporte a histórico de rotas
- Análise de KPIs em série temporal
- Mobile app (React Native)

---

## Dúvidas?

- 💬 Abra uma **Discussion** no GitHub
- 📧 Entre em contato com os maintainers
- 📚 Veja o [README.md](../README.md) para visão geral
- 🔧 Veja [GUIA_TECNICO_APROFUNDADO.md](./GUIA_TECNICO_APROFUNDADO.md) para detalhes técnicos

---

**Obrigado por contribuir! 🎉**
