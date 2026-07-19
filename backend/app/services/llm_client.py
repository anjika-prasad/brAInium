import json
import logging
import re
from abc import ABC, abstractmethod
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMClient(ABC):
    @abstractmethod
    def complete(self, system: str, user: str, json_mode: bool = False) -> str:
        ...


class OpenAIClient(LLMClient):
    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=settings.openai_api_key)

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=3))
    def complete(self, system: str, user: str, json_mode: bool = False) -> str:
        kwargs = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = self._client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
            **kwargs,
        )
        return resp.choices[0].message.content


class GeminiClient(LLMClient):
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        self._model = genai.GenerativeModel(settings.gemini_model)

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=3))
    def complete(self, system: str, user: str, json_mode: bool = False) -> str:
        prompt = f"{system}\n\n{user}"
        if json_mode:
            prompt += "\n\nRespond with valid JSON only, no markdown fences."
        resp = self._model.generate_content(prompt)
        return resp.text


class LlamaClient(LLMClient):
    def __init__(self):
        import requests
        self._requests = requests
        self._base_url = settings.llama_base_url

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=3))
    def complete(self, system: str, user: str, json_mode: bool = False) -> str:
        payload = {
            "model": settings.llama_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        }
        if json_mode:
            payload["format"] = "json"
        resp = self._requests.post(f"{self._base_url}/api/chat", json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["message"]["content"]


class FallbackDemoClient(LLMClient):
    """Fallback LLM engine for offline / keyless demoing."""

    def complete(self, system: str, user: str, json_mode: bool = False) -> str:
        if json_mode:
            tags = re.findall(r"\b[A-Z]{1,3}-\d{2,4}[A-Z]?\b", user)
            mode = "hybrid" if tags else "vector"
            if "failed" in user.lower() or "how many" in user.lower() or "history" in user.lower():
                mode = "graph"
            return json.dumps({
                "mode": mode,
                "equipment_tags": tags or ["P-101"],
                "reasoning": "Determined operational context via industrial domain pattern extraction."
            })

        # Answer generation fallback based on retrieved context
        if "SOP" in user or "LOTO" in user or "V-204A" in user:
            return (
                "Per [SOP_LOTO_V204A.txt], the Lockout/Tagout procedure for isolation valve V-204A and pump P-101 requires:\n"
                "1. Notify Unit 12 Operations Officer.\n"
                "2. Isolate main power at MCC Panel-4, Breaker B-12 (Motor M-101) with a red padlock.\n"
                "3. Manually close suction valve V-204A and apply a yellow lockout tag.\n"
                "4. Open bleed valve V-204C and verify local pressure gauge PG-101 shows 0.0 PSIG."
            )
        elif "fail" in user.lower() or "root cause" in user.lower() or "incident" in user.lower():
            return (
                "Based on knowledge graph synthesis across incident reports [INC_2025_01_P101.txt] and [INC_2025_02_P101.txt]:\n\n"
                "Crude Pump P-101 suffered two major outages in 2025:\n"
                "• **Incident 1 (2025-06-02)**: Mechanical seal fracture causing 14.5h downtime. **Root Cause**: Suction strainer S-101 particulate blockage starved Plan 11 seal flush cooling.\n"
                "• **Incident 2 (2025-07-11)**: Drive-end bearing SKF 6314-C3 failure causing 8.0h downtime. **Root Cause**: Shaft misalignment following June emergency seal work coupled with deferred vibration warning from report [INSP_2025_P101.txt]."
            )
        else:
            return (
                "According to plant document records [WO_8842_P101.txt] and [INSP_2025_P101.txt]:\n"
                "Pump P-101 underwent mechanical seal packing replacement under Work Order WO-8842 by technician J. Miller. "
                "Subsequent reliability inspection IR-2025-0589 by S. Kumar recorded 4.2 g's vibration and 78°C bearing temperature, recommending alignment and bearing replacement."
            )


_CLIENTS = {
    "openai": OpenAIClient,
    "gemini": GeminiClient,
    "llama": LlamaClient,
    "demo": FallbackDemoClient,
}

_singleton: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _singleton
    if _singleton is None:
        provider = settings.llm_provider.lower()
        if provider == "openai" and not settings.openai_api_key:
            provider = "demo"
        elif provider == "gemini" and not settings.gemini_api_key:
            provider = "demo"

        provider_cls = _CLIENTS.get(provider, FallbackDemoClient)
        try:
            _singleton = provider_cls()
        except Exception as e:
            logger.warning(f"Could not initialize {provider} LLM client ({e}), defaulting to demo client.")
            _singleton = FallbackDemoClient()

    return _singleton


def safe_json_parse(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": "failed_to_parse", "raw": raw}
