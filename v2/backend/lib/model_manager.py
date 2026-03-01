"""
Model Manager for Sasha AI v2

Generates responses via Ollama, augmenting the system prompt with
RAG-retrieved context chunks for each query.
"""

import logging
import httpx
from config.app_config import config
from lib.knowledge_manager import build_base_system_prompt, get_fallback_prompt

logger = logging.getLogger("sasha.model")


class ModelManager:
    def __init__(self):
        self.ollama_url = config.OLLAMA_URL
        self.ollama_model = config.OLLAMA_MODEL
        self._rag_available = False

    def load_model(self) -> None:
        """Check Ollama reachability and verify both LLM and embed models."""
        try:
            r = httpx.get(f"{self.ollama_url}/api/tags", timeout=5)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                if any(self.ollama_model in m for m in models):
                    logger.info(f"LLM model '{self.ollama_model}' is available.")
                else:
                    logger.warning(
                        f"LLM model '{self.ollama_model}' not found. "
                        f"Run: ollama pull {self.ollama_model}"
                    )
                if any(config.OLLAMA_EMBED_MODEL in m for m in models):
                    logger.info(f"Embed model '{config.OLLAMA_EMBED_MODEL}' is available.")
                    self._rag_available = True
                else:
                    logger.warning(
                        f"Embed model '{config.OLLAMA_EMBED_MODEL}' not found. "
                        f"RAG disabled. Run: ollama pull {config.OLLAMA_EMBED_MODEL}"
                    )
                    self._rag_available = False
            else:
                logger.warning(f"Ollama returned status {r.status_code}")
        except Exception as e:
            logger.warning(f"Could not reach Ollama at {self.ollama_url}: {e}")

    def _build_system_prompt(self, user_message: str) -> str:
        """
        Build the system prompt for this specific query.
        If RAG is available, retrieve relevant chunks and inject them.
        Otherwise fall back to the full static prompt.
        """
        if not self._rag_available:
            return get_fallback_prompt()

        try:
            from lib.rag_engine import rag_engine
            rag_context = rag_engine.build_rag_context(user_message)
            base = build_base_system_prompt()
            if rag_context:
                return base + rag_context
            else:
                # Nothing retrieved — fall back so Sasha still has some context
                return get_fallback_prompt()
        except Exception as e:
            logger.warning(f"RAG context build failed, using fallback: {e}")
            return get_fallback_prompt()

    def generate_response(
        self,
        user_message: str,
        conversation_history: list | None = None,
        system_prompt_override: str | None = None,
    ) -> str:
        """Generate a response via the Ollama chat API."""
        if system_prompt_override:
            system_prompt = system_prompt_override
        else:
            system_prompt = self._build_system_prompt(user_message)

        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            # Keep last 20 messages (10 turns)
            messages.extend(conversation_history[-20:])

        messages.append({"role": "user", "content": user_message})

        try:
            r = httpx.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": config.TEMPERATURE,
                        "num_predict": config.MAX_NEW_TOKENS,
                        "num_ctx": config.NUM_CTX,
                    },
                },
                timeout=90,
            )
            r.raise_for_status()
            return r.json()["message"]["content"].strip()
        except httpx.TimeoutException:
            return "SASHA_OFFLINE"
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return "SASHA_OFFLINE"

    def get_status(self) -> dict:
        try:
            r = httpx.get(f"{self.ollama_url}/api/tags", timeout=5)
            ollama_running = r.status_code == 200
        except Exception:
            ollama_running = False

        return {
            "backend": "ollama",
            "model": self.ollama_model,
            "embed_model": config.OLLAMA_EMBED_MODEL,
            "ollama_url": self.ollama_url,
            "ollama_running": ollama_running,
            "rag_available": self._rag_available,
        }


model_manager = ModelManager()
