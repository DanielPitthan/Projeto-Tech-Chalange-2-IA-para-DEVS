SYSTEM_PROMPT = (
    "Você é um(a) despachante logístico hospitalar. Gere instruções detalhadas e seguras com base no JSON "
    "fornecido, sem inventar dados. Priorize medicamentos críticos e oriente sobre segurança e conformidade."
)

INSTRUCTION_TEMPLATE = (
    "Aqui está o JSON da rota do veículo {vehicle_id}: {route_json}. "
    "Gere um passo-a-passo claro com tempos estimados, cuidados especiais e pontos de atenção."
)

REPORT_TEMPLATE = (
    "Aqui está o JSON global da solução e o baseline: solução={solution_json}, baseline={baseline_json}. "
    "Produza relatório executivo com comparativos, KPI e recomendações."
)

QA_TEMPLATE = "Com base no JSON de solução, responda: {question}."
