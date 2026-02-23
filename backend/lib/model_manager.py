"""
Model Management for Sasha AI
Handles generating responses via the local Ollama API
"""

import httpx
from config.app_config import config
from lib.knowledge_manager import get_system_prompt


class ModelManager:
    def __init__(self):
        self.use_trained_model = True  # Ollama is always "ready"
        self.ollama_url = config.OLLAMA_URL
        self.ollama_model = config.OLLAMA_MODEL

    def load_model(self, model_path: str = None):
        """Check that Ollama is reachable"""
        try:
            response = httpx.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = [m["name"] for m in response.json().get("models", [])]
                if any(self.ollama_model in m for m in models):
                    print(f"Ollama model '{self.ollama_model}' is available.")
                else:
                    print(f"WARNING: Model '{self.ollama_model}' not found in Ollama. Run: ollama pull {self.ollama_model}")
            else:
                print(f"WARNING: Ollama returned status {response.status_code}")
        except Exception as e:
            print(f"WARNING: Could not reach Ollama at {self.ollama_url}: {e}")
            print("Make sure Ollama is running: ollama serve")

    def generate_response(self, user_message: str, conversation_history: list = None, system_prompt_override: str = None) -> str:
        """Generate a response via the Ollama API"""
        prompt = system_prompt_override if system_prompt_override else get_system_prompt()
        messages = [{"role": "system", "content": prompt}]

        if conversation_history:
            messages.extend(conversation_history[-20:])  # last 10 turns (user+assistant pairs)

        messages.append({"role": "user", "content": user_message})

        try:
            response = httpx.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": config.TEMPERATURE,
                        "num_predict": config.MAX_NEW_TOKENS,
                        "num_ctx": 4096,
                    },
                },
                timeout=60,
            )
            response.raise_for_status()
            return response.json()["message"]["content"].strip()
        except httpx.TimeoutException:
            return "SASHA_OFFLINE"
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return "SASHA_OFFLINE"

    def get_status(self) -> dict:
        """Get current model status"""
        try:
            response = httpx.get(f"{self.ollama_url}/api/tags", timeout=5)
            ollama_running = response.status_code == 200
        except Exception:
            ollama_running = False

        return {
            "backend": "ollama",
            "model": self.ollama_model,
            "ollama_url": self.ollama_url,
            "ollama_running": ollama_running,
        }


# Global model manager instance
model_manager = ModelManager()
