from __future__ import annotations

import json
from typing import Any, Dict, Optional

try:
    from ollama import Client
except Exception:  # pragma: no cover
    Client = None  # type: ignore

from . import prompts


class LLMClient:
    """Cliente LLM exclusivo para Ollama local."""

    def __init__(self, model: str, temperature: float = 0.2, host: Optional[str] = None) -> None:
        self.model = model
        self.temperature = temperature
        self.host = host
        self.client: Optional[Client] = None
        self.available = False

        if Client is not None:
            # host opcional permite apontar para outra instância; default usa localhost:11434
            self.client = Client(host=host) if host else Client()
            self.available = True

    def complete(self, system: str, user: str) -> str:
        if not self.available or self.client is None:
            return "[LLM desabilitado: instale o pacote 'ollama' (pip install ollama) e execute 'ollama serve']"

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
            return f"[Erro ao chamar Ollama: {e}]"

        # resp.message.content já contém o texto final; manter fallback seguro
        try:
            return resp.message.content or ""
        except Exception:
            return ""


def instructions_for_route(client: LLMClient, vehicle_id: str, route_json: Dict[str, Any]) -> str:
    prompt = prompts.INSTRUCTION_TEMPLATE.format(vehicle_id=vehicle_id, route_json=json.dumps(route_json))
    return client.complete(prompts.SYSTEM_PROMPT, prompt)


def executive_report(client: LLMClient, solution_json: Dict[str, Any], baseline_json: Dict[str, Any]) -> str:
    prompt = prompts.REPORT_TEMPLATE.format(
        solution_json=json.dumps(solution_json), baseline_json=json.dumps(baseline_json)
    )
    return client.complete(prompts.SYSTEM_PROMPT, prompt)


def answer_question(client: LLMClient, solution_json: Dict[str, Any], question: str) -> str:
    prompt = prompts.QA_TEMPLATE.format(question=question + " (use apenas os dados fornecidos)")
    return client.complete(prompts.SYSTEM_PROMPT, prompt + json.dumps(solution_json))
