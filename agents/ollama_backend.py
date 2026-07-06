import os
from typing import List, Optional

import httpx


class OllamaBackend:
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None, timeout: float = 180.0) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL")
        self.timeout = timeout

    def list_models(self) -> List[str]:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            models = payload.get("models", [])
            return [model.get("name") for model in models if model.get("name")]
        except (httpx.HTTPError, ValueError, KeyError):
            return []

    def resolve_model_name(self, preferred_model: Optional[str] = None) -> str:
        candidates: List[str] = []
        if preferred_model:
            candidates.append(preferred_model)
        if self.model:
            candidates.append(self.model)
        if not candidates:
            candidates.append("mistral:latest")

        available_models = self.list_models()
        for candidate in candidates:
            if candidate in available_models:
                return candidate

        if available_models:
            return available_models[0]

        return candidates[0]

    def generate_text(self, prompt: str, model: Optional[str] = None) -> str:
        selected_model = self.resolve_model_name(model)
        payload = {"model": selected_model, "prompt": prompt, "stream": False}
        response = httpx.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    def health_check(self) -> bool:
        return bool(self.list_models())
