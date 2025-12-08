# Guia Técnico Aprofundado - Cacheiro VRP GA

Documentação técnica detalhada de cada componente, decisões arquiteturais e padrões de código.

## Índice

1. [Arquitetura Geral](#arquitetura-geral)
2. [Módulo Core (GA)](#módulo-core-ga)
3. [Módulo I/O](#módulo-io)
4. [Módulo LLM](#módulo-llm)
5. [Módulo Viz (Visualização)](#módulo-viz-visualização)
6. [Modelo de Dados](#modelo-de-dados)
7. [Padrões de Código](#padrões-de-código)
8. [Performance e Otimização](#performance-e-otimização)
9. [Extensões Futuras](#extensões-futuras)

---

## Arquitetura Geral

### Visão de Camadas

```
┌──────────────────────────────────────────────────────┐
│              UI Layer                                │
│  ┌──────────────┐              ┌─────────────┐      │
│  │ Streamlit    │              │ CLI         │      │
│  │ (app.py)     │              │ (cli.py)    │      │
│  └──────────────┘              └─────────────┘      │
└──────────────────────────────────────────────────────┘
                         │
┌──────────────────────────────────────────────────────┐
│          Business Logic Layer                        │
│  ┌──────────────────────────────────────────┐       │
│  │ GA (core/ga.py)                          │       │
│  │  ├─ initial_population()                 │       │
│  │  ├─ evolve()                             │       │
│  │  ├─ run()                                │       │
│  │  └─ crossover(), mutate()                │       │
│  └──────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────┘
                         │
┌──────────────────────────────────────────────────────┐
│          Optimization Layer                          │
│  ┌────────────┐ ┌───────────┐ ┌───────────┐       │
│  │ fitness.py │ │ selection │ │ heuristics│       │
│  └────────────┘ └───────────┘ └───────────┘       │
│  ┌────────────┐ ┌───────────┐ ┌───────────┐       │
│  │ distance.py│ │ vrp.py    │ │ mutation  │       │
│  └────────────┘ └───────────┘ └───────────┘       │
└──────────────────────────────────────────────────────┘
                         │
┌──────────────────────────────────────────────────────┐
│          Data & External Layer                       │
│  ┌──────────────┐  ┌──────────────┐ ┌────────────┐ │
│  │ io/          │  │ llm/         │ │ viz/       │ │
│  │ ├─ config.py │  │ ├─ render.py  │ │ ├─ map.py  │ │
│  │ ├─ load.py   │  │ └─ prompts.py │ │ └─ chart.py│ │
│  │ └─ save.py   │  │              │ │            │ │
│  └──────────────┘  └──────────────┘ └────────────┘ │
│                                                     │
│  External: YAML, CSV, OpenAI API, Gemini API       │
└──────────────────────────────────────────────────────┘
```

### Fluxo de Dados

```
config.yaml ──────┐
                  ├─► ConfigLoader ──► Config (dataclass)
                  │                        │
                  │                        ▼
                  │                    run_optimizer()
                  │                        │
capitais.csv ─────┼─► load_nodes() ──► Dict[Node]
                  │       │                │
                  │       └──► validate_nodes()
                  │                        │
                  ▼                        ▼
              ┌───────────────────────────────┐
              │   GeneticAlgorithm(...)       │
              │   ├─ initial_population()     │
              │   ├─ evolve() × N gerações   │
              │   └─ run() → best_indiv      │
              └───────────────────────────────┘
                      │
                      ▼
              evaluate_individual()
                      │
                      ▼
              ┌──────────────────────────────┐
              │  Routes + Convergence        │
              │  + Global Metrics            │
              └──────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
    JSON        map.html        report.md
   outputs/
```

---

## Módulo Core (GA)

### core/ga.py - Algoritmo Genético

**Classe Principal:** `GeneticAlgorithm`

```python
class GeneticAlgorithm:
    def __init__(self, nodes_map, depot, ga_params, vrp_params, weights):
        self.nodes_map = nodes_map          # Dict[id -> Node]
        self.depot = depot                  # Node (depósito)
        self.ga = ga_params                 # GAParams (config)
        self.vrp = vrp_params               # VRPParams (config)
        self.weights = weights              # WeightParams (config)
```

#### Método: `initial_population(base_orders)`

```python
def initial_population(self, base_orders: List[Sequence[int]]) -> List[Individual]:
    # Individual = List[int] (permutação de node_ids)
    
    population = []
    node_ids = [nid for nid in self.nodes_map if nid != self.depot.node_id]
    
    # Cria indivíduos aleatórios
    for _ in range(self.ga.population_size - len(base_orders)):
        indiv = node_ids[:]
        random.shuffle(indiv)                    # Shuffle em-place
        population.append(indiv)
    
    # Adiciona seeds heurísticos (ex: Nearest Neighbor)
    population.extend([list(order) for order in base_orders])
    
    return population[: self.ga.population_size]
```

**Fluxo:**
1. Extrai IDs dos nós (exclui depósito)
2. Cria N-K indivíduos aleatórios (K = tamanho de base_orders)
3. Adiciona K seeds heurísticos
4. Retorna primeiros population_size (descarta excesso)

**Exemplo:**
```
node_ids = [1, 2, 3, 4, 5, 6, 7, 8]  (excluindo 0=depot)
population_size = 150
base_orders = [[3,1,5,2,4,7,6,8]]    (Nearest Neighbor)

→ Cria 149 shuffles aleatórios + 1 seed NN
→ Retorna lista com 150 indivíduos
```

#### Método: `crossover(parent1, parent2)`

```python
def crossover(self, parent1, parent2) -> Tuple[Individual, Individual]:
    if random.random() > self.ga.crossover_rate:
        # Sem crossover (90% de chance): copia pais
        return parent1[:], parent2[:]
    
    if self.ga.crossover.upper() == "PMX":
        return pmx(parent1, parent2)
    elif self.ga.crossover.upper() == "OX":
        return ox(parent1, parent2)
    else:
        raise ValueError(f"Unsupported crossover {self.ga.crossover}")
```

**Fluxo:**
1. Verifica taxa de crossover (padrão 90%)
2. Se random > 0.9: retorna cópias dos pais (10% chance)
3. Senão: aplica PMX ou OX

#### Método: `evolve(population)`

Aqui ocorre a seleção, crossover, mutação e avaliação de uma geração.

```python
def evolve(self, population) -> Tuple[List[Individual], List[float], List[List]]:
    fitness_values = []
    decoded_routes = []
    
    # 1. Avalia população atual
    for indiv in population:
        fit, routes = evaluate_individual(indiv, ...)
        fitness_values.append(fit)
        decoded_routes.append(routes)
    
    new_population = []
    
    # 2. Elitismo: preserva K melhores indivíduos
    elite_indices = sorted(range(len(population)), 
                          key=lambda i: fitness_values[i])[:self.ga.elitism]
    for idx in elite_indices:
        new_population.append(population[idx])
    
    # 3. Cria nova população por seleção, crossover, mutação
    while len(new_population) < self.ga.population_size:
        # Seleção: escolhe 2 pais
        parent1, parent2 = select_pair(population, fitness_values, ...)
        
        # Crossover
        child1, child2 = self.crossover(parent1, parent2)
        
        # Mutação
        if random.random() < self.ga.mutation_rate:
            child1 = mutate(child1, self.ga.mutation)
        if random.random() < self.ga.mutation_rate:
            child2 = mutate(child2, self.ga.mutation)
        
        # Adiciona à nova população
        new_population.append(child1)
        if len(new_population) < self.ga.population_size:
            new_population.append(child2)
    
    return new_population, fitness_values, decoded_routes
```

**Passos:**
1. **Avaliação:** Calcula fitness de cada indivíduo
2. **Elitismo:** Copia K melhores para nova população
3. **Preenchimento:** Seleciona pares, faz crossover, mutação
4. **Retorno:** Nova população, fitnesses, rotas decodificadas

#### Método: `run(base_orders)`

Loop principal do GA.

```python
def run(self, base_orders) -> Tuple[Individual, float, List[float], List[List]]:
    population = self.initial_population(base_orders)
    best_fitness = float("inf")
    best_individual = None
    convergence = []
    stagnant = 0
    
    for gen in range(self.ga.generations):
        # Evolui uma geração
        population, fitness_vals, decoded = self.evolve(population)
        
        # Encontra melhor da geração
        gen_best_idx = min(range(len(fitness_vals)), 
                          key=lambda i: fitness_vals[i])
        gen_best_fit = fitness_vals[gen_best_idx]
        
        # Atualiza melhor global
        if gen_best_fit < best_fitness:
            best_fitness = gen_best_fit
            best_individual = population[gen_best_idx]
            stagnant = 0
        else:
            stagnant += 1
        
        # Registra convergência
        convergence.append(gen_best_fit)
        
        # Parada por estagnação
        if stagnant >= self.ga.stagnation_patience:
            print(f"Early stopping at gen {gen+1}")
            break
    
    return best_individual, best_fitness, convergence, decoded
```

**Lógica:**
1. Inicializa população
2. Para cada geração:
   - Evolui população
   - Encontra melhor fitness da geração
   - Atualiza melhor global e contador de estagnação
   - Registra convergência
   - Se estagnado por 30 gerações: para
3. Retorna melhor solução

---

### core/fitness.py - Função de Avaliação

```python
def evaluate_individual(
    permutation: Sequence[int],
    nodes_map: Dict[int, Node],
    depot: Node,
    vrp: VRPParams,
    weights: WeightParams,
) -> tuple[float, List[RouteMetrics]]:
    # 1. Divide permutação em rotas
    routes = split_routes(permutation, nodes_map, depot, vrp)
    
    # 2. Calcula métricas de cada rota
    total_distance = 0.0
    total_penalty = {"capacity": 0.0, "range": 0.0, "priority": 0.0, "time": 0.0}
    
    for route in routes:
        metrics = compute_route_metrics(route, nodes_map, depot, vrp, weights)
        total_distance += metrics.distance_km
        for key, val in metrics.penalties.items():
            total_penalty[key] += val
    
    # 3. Calcula fitness como combinação linear
    fitness = (
        weights.w_distance * total_distance
        + weights.w_capacity * total_penalty["capacity"]
        + weights.w_range * total_penalty["range"]
        + weights.w_priority * total_penalty["priority"]
        + weights.w_time * total_penalty["time"]
    )
    
    return fitness, routes
```

**Componentes:**

#### Função: `split_routes()`

Divide permutação em rotas respeitando capacidade.

```python
def split_routes(permutation, nodes_map, depot, vrp):
    routes = []
    current_route = [depot.node_id]
    current_load = 0
    
    for node_id in permutation:
        node = nodes_map[node_id]
        
        # Se adicionar nó ultrapassa capacidade: nova rota
        if current_load + node.demand > vrp.vehicle_capacity:
            current_route.append(depot.node_id)  # Retorna ao depot
            routes.append(Route(sequence=current_route, ...))
            current_route = [depot.node_id]
            current_load = 0
        
        current_route.append(node_id)
        current_load += node.demand
    
    # Fecha última rota
    current_route.append(depot.node_id)
    routes.append(Route(sequence=current_route, ...))
    
    return routes
```

**Exemplo:**
```
Permutação: [5, 3, 8, 1, 2, 7, 4, 6]
Capacidade: 80

Route 1: [0, 5(10), 3(15), 8(20), 1(25)] → carga=70
         Tentar adicionar 2(15): 70+15=85 > 80 → NOVA ROTA

Route 2: [0, 2(15), 7(30), 4(25)] → carga=70
         Tentar adicionar 6(10): 70+10=80 → OK

Route 3: [0, 6(10), 0] → carga=10

Resultado: 3 rotas
```

#### Função: `compute_route_metrics()`

Calcula distância, tempo, penalidades de uma rota.

```python
def compute_route_metrics(route, nodes_map, depot, vrp, weights):
    distance_km = 0.0
    time_min = 0.0
    load = 0.0
    penalties = {"capacity": 0.0, "range": 0.0, "priority": 0.0, "time": 0.0}
    
    # Distância e tempo entre nós
    for i in range(len(route.sequence) - 1):
        from_id = route.sequence[i]
        to_id = route.sequence[i + 1]
        
        from_node = nodes_map[from_id]
        to_node = nodes_map[to_id]
        
        dist = haversine(from_node.lat, from_node.lon, 
                        to_node.lat, to_node.lon)
        distance_km += dist
        time_min += (dist / vrp.vehicle_speed_kmh) * 60
        
        # Serviço
        if to_id != depot.node_id:
            time_min += vrp.service_time_min
        
        load += to_node.demand if to_id != depot.node_id else 0
    
    # Penalidades
    if load > vrp.vehicle_capacity:
        penalties["capacity"] = (load - vrp.vehicle_capacity) * weights.w_capacity
    
    if distance_km > vrp.vehicle_range_km:
        penalties["range"] = (distance_km - vrp.vehicle_range_km) * weights.w_range
    
    # (outras penalidades)
    
    return RouteMetrics(
        sequence=route.sequence,
        distance_km=distance_km,
        time_min=time_min,
        load=load,
        penalties=penalties
    )
```

---

### core/selection.py - Seleção

Implementa Tournament e Roulette selection.

```python
def select_pair(population, fitness_values, method, tournament_k):
    if method == "tournament":
        parent1 = tournament_selection(population, fitness_values, tournament_k)
        parent2 = tournament_selection(population, fitness_values, tournament_k)
    elif method == "roulette":
        parent1 = roulette_selection(population, fitness_values)
        parent2 = roulette_selection(population, fitness_values)
    else:
        raise ValueError(f"Unknown selection method: {method}")
    
    return parent1, parent2

def tournament_selection(population, fitness_values, k):
    # Escolhe k indivíduos aleatórios
    candidates = random.sample(range(len(population)), k)
    
    # Retorna o melhor (menor fitness)
    best_idx = min(candidates, key=lambda i: fitness_values[i])
    return population[best_idx]

def roulette_selection(population, fitness_values):
    # Inverte fitness (mínimo = máximo)
    inverted = [max(fitness_values) - f for f in fitness_values]
    
    # Cria roda proporcional ao fitness
    total = sum(inverted)
    pick = random.uniform(0, total)
    
    current = 0
    for i, fitness in enumerate(inverted):
        current += fitness
        if current > pick:
            return population[i]
    
    return population[-1]
```

**Comparação:**

| Aspecto | Tournament | Roulette |
|---------|-----------|----------|
| **Seleção** | k aleatórios, melhor vence | Proporcional ao fitness |
| **Pressão** | Controlável (k) | Alta (super-fit domina) |
| **Diversidade** | Preserva melhor | Reduz rápido |
| **Convergência** | Estável | Pode ser prematura |

---

### core/crossover.py - Crossover

#### PMX (Partially Mapped Crossover)

```python
def pmx(parent1, parent2):
    n = len(parent1)
    
    # Escolhe 2 pontos de corte
    c1, c2 = sorted(random.sample(range(n), 2))
    
    # Cria segmento do pai2
    child1 = parent1[:]
    segment = parent2[c1:c2]
    
    # Cria mapa de ciclo
    mapping = {}
    for i, val in enumerate(segment):
        pos_in_p1 = parent1.index(val)
        mapping[parent1[c1 + i]] = val
    
    # Preenche child1 com mapa
    for i in range(c1, c2):
        child1[i] = parent2[i]
    
    # Resolve conflitos (mesmo processo para child2)
    # ...
    
    return child1, child2
```

**Visualização:**
```
Parent 1: [1 | 2 3 4 5 | 6 7 8]
Parent 2: [3 | 4 5 6 7 | 1 2 8]
          └──────┬──────┘
          (pontos de corte: 1,5)

Mapa: {2→4, 3→5, 4→6, 5→7}

Child1:  [1 | 4 5 6 7 | 3 2 8]  (resolve via mapa)
Child2:  [3 | 2 3 4 5 | 1 6 8]  (inverso)
```

#### OX (Order Crossover)

```python
def ox(parent1, parent2):
    n = len(parent1)
    c1, c2 = sorted(random.sample(range(n), 2))
    
    # Child herda segmento do parent1
    child = [-1] * n
    child[c1:c2] = parent1[c1:c2]
    
    # Preenche restante na ordem de parent2
    ptr_parent = c2
    ptr_child = c2
    
    while ptr_child - c1 < n:
        if ptr_parent >= n:
            ptr_parent = 0
        
        if parent2[ptr_parent] not in child[c1:c2]:
            if ptr_child >= n:
                ptr_child = 0
            child[ptr_child] = parent2[ptr_parent]
            ptr_child += 1
        
        ptr_parent += 1
    
    return child, ox(parent2, parent1)[0]  # Cria outro child simetricamente
```

---

### core/mutation.py - Mutação

#### Swap Mutation

```python
def swap_mutation(individual):
    indiv = individual[:]
    i, j = random.sample(range(len(indiv)), 2)
    indiv[i], indiv[j] = indiv[j], indiv[i]  # Troca
    return indiv
```

#### Inversion Mutation

```python
def inversion_mutation(individual):
    indiv = individual[:]
    i, j = sorted(random.sample(range(len(indiv)), 2))
    indiv[i:j+1] = indiv[i:j+1][::-1]  # Inverte
    return indiv
```

**Diferença:**
- **Swap:** 2-opt local (muda vizinhos imediatos)
- **Inversion:** Pode afetar segmentos longos (maior disrupção)

---

### core/heuristics.py - Heurísticas

#### Nearest Neighbor

```python
def nearest_neighbor_order(unvisited, nodes_map, depot):
    route = [depot.node_id]
    current = depot
    unvisited_list = list(unvisited)
    
    while unvisited_list:
        # Encontra vizinho mais próximo
        nearest = min(
            unvisited_list,
            key=lambda nid: haversine(
                current.lat, current.lon,
                nodes_map[nid].lat, nodes_map[nid].lon
            )
        )
        
        route.append(nearest)
        current = nodes_map[nearest]
        unvisited_list.remove(nearest)
    
    return route
```

**Complexidade:** O(n²)  
**Qualidade:** Tipicamente 80-90% do ótimo  
**Uso:** Seed inicial para GA

---

### core/distance.py - Cálculo de Distância

#### Haversine Formula

```python
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Raio da Terra em km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat/2)**2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon/2)**2)
    
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c
```

**Precisão:** ~0.5% de erro  
**Complexidade:** O(1)

---

## Módulo I/O

### io/config.py - Carregamento de Configuração

```python
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
        
        # Parse cada seção
        ga = GAParams(...)
        vrp = VRPParams(...)
        weights = WeightParams(...)
        depot = Node(...)
        
        return Config(ga=ga, vrp=vrp, weights=weights, depot=depot, ...)
```

**Validações:**
- ✅ Arquivo YAML válido
- ✅ Tipos corretos (int, float, str)
- ✅ Valores dentro de ranges esperados
- ❌ Sem validação de valores anormais (ex: população=-1)

**Melhorias futuras:**
```python
# Adicionar validações em ConfigLoader
if ga['population_size'] < 10:
    raise ValueError("population_size deve ser >= 10")
```

---

### io/load_data.py - Carregamento de Dados

```python
def load_nodes(csv_path: str | Path) -> Dict[int, Node]:
    df = pd.read_csv(csv_path)
    nodes = {}
    
    for _, row in df.iterrows():
        node = Node(
            node_id=int(row['id']),
            name=row['nome'],
            state=row['estado'],
            lat=float(row['latitude']),
            lon=float(row['longitude']),
            demand=float(row['demanda']),
            priority=int(row['prioridade']),
            window_start=row.get('janela_inicio'),
            window_end=row.get('janela_fim'),
            service_time_min=int(row.get('tempo_atendimento_min', 10))
        )
        nodes[node.node_id] = node
    
    return nodes

def validate_nodes(nodes: Dict[int, Node]) -> List[str]:
    errors = []
    
    for nid, node in nodes.items():
        # Validações
        if not (-90 <= node.lat <= 90):
            errors.append(f"Latitude inválida no nó {nid}")
        if not (-180 <= node.lon <= 180):
            errors.append(f"Longitude inválida no nó {nid}")
        if node.demand < 0:
            errors.append(f"Demanda negativa no nó {nid}")
        if node.priority not in [1, 2, 3]:
            errors.append(f"Prioridade inválida no nó {nid}")
    
    return errors
```

**Colunas esperadas:**
```
id (int): Identificador único
nome (str): Nome do local
estado (str): UF (ex: SP, RJ)
latitude (float): Coordenada Y
longitude (float): Coordenada X
demanda (float): Quantidade a entregar
prioridade (int): 1=crítica, 2=alta, 3=normal
janela_inicio (str): Horário início (ex: 08:00)
janela_fim (str): Horário fim (ex: 20:00)
tempo_atendimento_min (int): Minutos de serviço
```

---

### io/output_saver.py - Salvamento de Saídas

```python
def save_json(data: Dict, path: str | Path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_md(content: str, path: str | Path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def save_log_records(records: List[Dict], path: str | Path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
```

---

## Módulo LLM

### llm/render.py - Cliente LLM

```python
class LLMClient:
    def __init__(self, model, api_key=None, temperature=0.2, provider="openai"):
        self.model = model
        self.temperature = temperature
        self.api_key = api_key
        self.provider = provider.lower()
        
        self.client = None
        self.available = False
        
        # Inicializa cliente apropriado
        if self.provider == "openai" and OpenAI and api_key:
            self.client = OpenAI(api_key=api_key)
            self.available = True
        elif self.provider == "gemini" and genai and api_key:
            genai.configure(api_key=api_key)
            self.available = True
        elif self.provider == "local":
            self.available = True

    def complete(self, system: str, user: str) -> str:
        if not self.available:
            return "[LLM desabilitado: configure chave e provider]"
        
        if self.provider == "openai":
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ]
            )
            return resp.choices[0].message.content or ""
        
        elif self.provider == "gemini":
            model = genai.GenerativeModel(self.model)
            resp = model.generate_content(f"SYSTEM:\n{system}\n\nUSER:\n{user}")
            return resp.text or ""
        
        else:  # local
            return "[LLM local/mock: nenhuma chamada externa]"
```

**Fluxo de Erro:**
```
    Sem API Key?
    ├─ Se provider != "local": retorna mensagem de erro
    └─ Se provider == "local": usa stub (sem custo)
```

---

### llm/prompts.py - Templates

```python
SYSTEM_PROMPT = """
Você é um(a) despachante logístico hospitalar. Gere instruções detalhadas
e seguras com base no JSON fornecido, sem inventar dados. Priorize medicamentos
críticos e oriente sobre segurança e conformidade.
"""

INSTRUCTION_TEMPLATE = """
Aqui está o JSON da rota do veículo {vehicle_id}:

{route_json}

Gere um passo-a-passo claro com:
1. Ordem de paradas
2. Tempos estimados
3. Cuidados especiais
4. Pontos de atenção e validações
"""

REPORT_TEMPLATE = """
Aqui está a solução global e baseline de comparação:

SOLUÇÃO: {solution_json}
BASELINE: {baseline_json}

Produza um relatório executivo com:
1. Comparativos de KPI
2. Análise de melhoria
3. Recomendações
"""

QA_TEMPLATE = """
Com base no JSON de solução, responda a pergunta:

{question}

Use apenas dados fornecidos, sem especulação.
"""
```

---

## Módulo Viz (Visualização)

### viz/map.py - Mapa Folium

```python
def render_map(depot, nodes_map, routes, output_path):
    # Cria mapa centrado no depósito
    m = folium.Map(
        location=[depot.lat, depot.lon],
        zoom_start=4
    )
    
    # Marca depósito
    folium.Marker(
        [depot.lat, depot.lon],
        popup=f"Depot: {depot.name}",
        icon=folium.Icon(color="black")
    ).add_to(m)
    
    # Marca clientes
    for node in nodes_map.values():
        if node.node_id == depot.node_id:
            continue
        
        # Cor por prioridade
        color = "red" if node.priority == 1 else \
                "orange" if node.priority == 2 else "blue"
        
        folium.CircleMarker(
            [node.lat, node.lon],
            radius=4,
            color=color,
            fill=True,
            popup=f"{node.name} (p{node.priority})"
        ).add_to(m)
    
    # Desenha rotas
    colors = ["red", "blue", "green", "purple", "orange", ...]
    for idx, route in enumerate(routes):
        coords = [[nodes_map[nid].lat, nodes_map[nid].lon] 
                  for nid in route.sequence]
        folium.PolyLine(
            coords,
            color=colors[idx % len(colors)],
            weight=4,
            opacity=0.8
        ).add_to(m)
    
    m.save(output_path)
```

---

### viz/charts.py - Gráficos

```python
def plot_convergence(convergence: List[float], output_path: str):
    plt.figure(figsize=(10, 6))
    plt.plot(convergence, label="Best Fitness", linewidth=2)
    plt.xlabel("Generation", fontsize=12)
    plt.ylabel("Fitness", fontsize=12)
    plt.title("GA Convergence", fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
```

---

## Modelo de Dados

### Dataclasses em core/vrp.py

```python
@dataclass
class Node:
    node_id: int
    name: str
    state: str
    lat: float
    lon: float
    demand: float
    priority: int          # 1=crítica, 2=alta, 3=normal
    window_start: str      # "08:00"
    window_end: str        # "20:00"
    service_time_min: int

@dataclass
class RouteMetrics:
    sequence: List[int]
    distance_km: float
    time_min: float
    load: float
    penalties: Dict[str, float]

@dataclass
class GAParams:
    seed: int
    population_size: int
    generations: int
    selection: str         # "tournament" ou "roulette"
    tournament_k: int
    crossover: str         # "PMX" ou "OX"
    crossover_rate: float
    mutation: str          # "swap" ou "inversion"
    mutation_rate: float
    elitism: int
    stagnation_patience: int

@dataclass
class VRPParams:
    vehicles: int
    vehicle_capacity: float
    vehicle_range_km: float
    vehicle_speed_kmh: float
    service_time_min: float
    work_time_window: List[str]

@dataclass
class WeightParams:
    w_distance: float
    w_capacity: float
    w_range: float
    w_priority: float
    w_time: float
```

---

## Padrões de Código

### 1. Type Hints

Todos os arquivos usam type hints (PEP 484):

```python
def evaluate_individual(
    permutation: Sequence[int],
    nodes_map: Dict[int, Node],
    depot: Node,
    vrp: VRPParams,
    weights: WeightParams,
) -> tuple[float, List[RouteMetrics]]:
    ...
```

**Benefício:** Type checking com Pylance, documentação automática.

### 2. Dataclasses

Config e modelos usam `@dataclass` (PEP 557):

```python
from dataclasses import dataclass

@dataclass
class Node:
    node_id: int
    name: str
    lat: float
    lon: float
```

**Benefício:** Sem `__init__`, `__repr__` automático, imutável com `frozen=True`.

### 3. Exceções Customizadas

Poderia adicionar:

```python
class VRPError(Exception):
    """Base exception for VRP issues."""
    pass

class ConfigError(VRPError):
    """Configuration loading error."""
    pass

class DataError(VRPError):
    """Data validation error."""
    pass
```

### 4. Context Managers

Salvamento de arquivos:

```python
def save_json(data, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f)
```

---

## Performance e Otimização

### Complexidade Algoritmo GA

```
Tempo total ≈ G × (P × F_time + GA_ops)

G = gerações (200)
P = população (150)
F_time = tempo fitness (~10ms)
GA_ops = seleção, crossover, mutação (~0.5ms)

Total ≈ 200 × (150 × 10ms + 0.5ms) ≈ 305 segundos
Mas: Early stopping reduz para ~30-120s típico
```

### Otimizações Implementadas

1. **Early Stopping:** Parada por estagnação (30 gerações)
2. **Elitismo:** Preserva melhores (5 indivíduos)
3. **Seeds Heurísticos:** Começa de bom ponto
4. **Lazy Evaluation:** Fitness calculado sob demanda

### Otimizações Futuras

1. **Paralelização:**
   ```python
   from multiprocessing import Pool
   with Pool(4) as p:
       fitnesses = p.map(evaluate_individual, population)
   ```

2. **Caching de Distâncias:**
   ```python
   @lru_cache(maxsize=512)
   def haversine(lat1, lon1, lat2, lon2):
       ...
   ```

3. **Numpy para Cálculos:**
   ```python
   import numpy as np
   distances = np.array([[haversine(...)] for ...])
   ```

---

## Extensões Futuras

### 1. Multi-Objetivo

Usar NSGA-II para otimizar simultaneamente distância + custo + emissões:

```python
from deap import base, creator, tools, algorithms

creator.create("FitnessMulti", base.Fitness, weights=(-1.0, -1.0, -1.0))
creator.create("Individual", list, fitness=creator.FitnessMulti)
```

### 2. Algoritmos Alternativos

- **Ant Colony Optimization (ACO):** Bom para VRP
- **Particle Swarm Optimization (PSO):** Alternativa GA
- **Tabu Search:** Busca local agressiva
- **Or-Tools:** Google's industrial solver

### 3. Restrições Avançadas

- Janela de tempo com chegada cumulativa
- Múltiplos depósitos
- Veículos heterogêneos (diferentes capacidades)
- Coleta e entrega (pickup/delivery)

### 4. Interface Web

```python
# Migrar para FastAPI + React
from fastapi import FastAPI

app = FastAPI()

@app.post("/optimize")
async def optimize(config: ConfigSchema, data: DataSchema):
    # ... GA execution ...
    return solution_json
```

### 5. Persistência

```python
# Salvar/carregar solutions em DB
import sqlalchemy
engine = sqlalchemy.create_engine("sqlite:///solutions.db")

class Solution(Base):
    id = Column(Integer, primary_key=True)
    routes = Column(JSON)
    fitness = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
```

---

**Fim do Guia Técnico Aprofundado**
