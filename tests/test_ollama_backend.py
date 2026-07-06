import httpx

from agents.ollama_backend import OllamaBackend


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("request failed", request=None, response=self)

    def json(self):
        return self._payload


def test_list_models_returns_available_names(monkeypatch):
    def fake_get(url, timeout):
        assert url.endswith("/api/tags")
        return FakeResponse({"models": [{"name": "mistral:latest"}, {"name": "llama3:latest"}]})

    monkeypatch.setattr("agents.ollama_backend.httpx.get", fake_get)

    backend = OllamaBackend(base_url="http://localhost:11434")
    assert backend.list_models() == ["mistral:latest", "llama3:latest"]


def test_resolve_model_name_prefers_available_model(monkeypatch):
    monkeypatch.setattr(
        "agents.ollama_backend.httpx.get",
        lambda url, timeout: FakeResponse({"models": [{"name": "mistral:latest"}]})
    )

    backend = OllamaBackend(base_url="http://localhost:11434", model="mistral:latest")
    assert backend.resolve_model_name("llama3:latest") == "mistral:latest"


def test_generate_text_uses_selected_model(monkeypatch):
    def fake_post(url, json, timeout):
        assert url.endswith("/api/generate")
        assert json["model"] == "mistral:latest"
        assert json["prompt"] == "Hello"
        assert json["stream"] is False
        return FakeResponse({"response": "Hi there"})

    monkeypatch.setattr("agents.ollama_backend.httpx.post", fake_post)
    monkeypatch.setattr(
        "agents.ollama_backend.httpx.get",
        lambda url, timeout: FakeResponse({"models": [{"name": "mistral:latest"}]})
    )

    backend = OllamaBackend(base_url="http://localhost:11434", model="mistral:latest")
    assert backend.generate_text("Hello") == "Hi there"


def test_health_check_returns_true_when_models_exist(monkeypatch):
    monkeypatch.setattr(
        "agents.ollama_backend.httpx.get",
        lambda url, timeout: FakeResponse({"models": [{"name": "mistral:latest"}]})
    )

    backend = OllamaBackend(base_url="http://localhost:11434")
    assert backend.health_check() is True
