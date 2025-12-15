# RELATORIO DE OTIMIZACAO DE ROTAS

**Data de Geracao:** 15/12/2025 19:29
**Periodo:** Diário

---

## 1. RESUMO EXECUTIVO

Esta otimizacao utilizou **5 veiculos** para realizar as entregas, 
percorrendo um total de **30870.77 km** em aproximadamente 
**23537 minutos**.

---

## 2. KPIs PRINCIPAIS

| Indicador | Valor | Variacao vs Baseline |
|-----------|-------|---------------------|
| Distancia Total (km) | 30870.77 | - |
| Tempo Total (min) | 23537 | - |
| Veiculos Utilizados | 5 | - |
| Carga Media (kg) | 82.80 | - |
| Desvio Padrao Carga | 18.31 | - |
| Fitness Final | 6002046.94 | - |

---

## 3. ANALISE DE VIOLACOES

- **V1**: Autonomia excedida (penalidade: 6226.62)
- **V1**: Prioridades não otimizadas (penalidade: 14.25)
- **V1**: Janela de tempo violada (penalidade: 75460.70)
- **V2**: Autonomia excedida (penalidade: 8126.95)
- **V2**: Prioridades não otimizadas (penalidade: 15.55)
- **V2**: Janela de tempo violada (penalidade: 44553.58)
- **V3**: Autonomia excedida (penalidade: 3530.76)
- **V3**: Prioridades não otimizadas (penalidade: 11.25)
- **V3**: Janela de tempo violada (penalidade: 19173.86)
- **V4**: Autonomia excedida (penalidade: 4314.41)
- **V4**: Prioridades não otimizadas (penalidade: 15.75)
- **V4**: Janela de tempo violada (penalidade: 37473.28)
- **V5**: Autonomia excedida (penalidade: 5672.02)
- **V5**: Prioridades não otimizadas (penalidade: 6.15)
- **V5**: Janela de tempo violada (penalidade: 38206.40)

---

## 4. DETALHAMENTO POR VEICULO

### V1
- **Rota:** 🏠 Depósito → Londrina → Ribeirão Preto → Uberlândia → Goiânia → Brasília → Palmas → Marabá → Belém → Ananindeua → Macapá → Santarém → Parintins → 🏠 Depósito
- **Distância:** 6826.62 km
- **Tempo:** 5210 min
- **Carga:** 92.0 kg

### V2
- **Rota:** 🏠 Depósito → Sorocaba → Paulínia → Campinas → Jundiaí → Rio de Janeiro → Belo Horizonte → Itacoatiara → Manaus → Boa Vista → Porto Velho → Rio Branco → 🏠 Depósito
- **Distância:** 8726.95 km
- **Tempo:** 6631 min
- **Carga:** 97.0 kg

### V3
- **Rota:** 🏠 Depósito → Santos → Curitiba → Joinville → Blumenau → Florianópolis → Caxias do Sul → Porto Alegre → Maringá → Campo Grande → Cuiabá → 🏠 Depósito
- **Distância:** 4130.76 km
- **Tempo:** 3178 min
- **Carga:** 85.0 kg

### V4
- **Rota:** 🏠 Depósito → São Paulo → Guarulhos → Vitória → Salvador → Feira de Santana → Maceió → Recife → João Pessoa → Natal → 🏠 Depósito
- **Distância:** 4914.41 km
- **Tempo:** 3766 min
- **Carga:** 93.0 kg

### V5
- **Rota:** 🏠 Depósito → Aracaju → Picos → Teresina → Parnaíba → Fortaleza → São Luís → 🏠 Depósito
- **Distância:** 6272.02 km
- **Tempo:** 4752 min
- **Carga:** 47.0 kg


---

## 5. ANALISE DE CONVERGENCIA

O algoritmo executou **208 geracoes**.

- **Fitness inicial:** 7691321.13
- **Fitness final:** 5979223.38
- **Melhoria:** 22.3%
- **Parou por:** Convergência por estagnação

---

## 6. RECOMENDACOES

Com base na analise dos dados:

1. **Autonomia:** Todas as rotas excedem a autonomia configurada. Considere aumentar o parametro `vehicle_range_km` ou adicionar mais veiculos.

2. **Balanceamento:** O desvio padrao de carga indica desbalanceamento entre veiculos. Ajuste os pesos da funcao fitness.

3. **Parametros AG:** Se a convergencia estagnou cedo, aumente `mutation_rate` ou `stagnation_patience`.
