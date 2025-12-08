from __future__ import annotations

import json
from typing import Any, Dict, Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover
    genai = None  # type: ignore

from . import prompts


class LLMClient:
    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.2,
        provider: str = "openai",
    ):
        self.model = model
        self.temperature = temperature
        self.api_key = api_key
        self.provider = provider.lower()

        self.client = None
        self.available = False

        if self.provider == "openai" and OpenAI is not None and api_key:
            self.client = OpenAI(api_key=api_key)
            self.available = True
        elif self.provider == "gemini" and genai is not None and api_key:
            genai.configure(api_key=api_key)
            self.available = True
        elif self.provider == "local":
            # local/mock provider: always available, no external calls
            self.available = True

    def complete(self, system: str, user: str) -> str:
        if not self.available:
            return "[LLM desabilitado: configure chave e provider (openai/gemini/local)]"

        if self.provider == "openai" and self.client:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            )
            return resp.choices[0].message.content or ""

        if self.provider == "gemini":
            if genai is None:
                return "[Gemini SDK ausente: instale google-generativeai]"
            model = genai.GenerativeModel(self.model)
            prompt = f"SYSTEM:\n{system}\n\nUSER:\n{user}"
            resp = model.generate_content(prompt)
            return resp.text or ""

        # Local/mock provider
        return "[LLM local/mock: nenhuma chamada externa realizada]"


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
