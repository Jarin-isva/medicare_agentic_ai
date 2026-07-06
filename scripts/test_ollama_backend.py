import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.ollama_backend import OllamaBackend


if __name__ == "__main__":
    backend = OllamaBackend(base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), timeout=180.0)
    print("Available models:", backend.list_models())
    print("Selected model:", backend.resolve_model_name())
    response = backend.generate_text("Say hello in one sentence.")
    print("Response:", response)
