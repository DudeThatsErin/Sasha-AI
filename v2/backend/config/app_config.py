"""
Configuration settings for Sasha AI v2
"""

import os


class Config:
    # API Settings
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "https://erinskidds.com",
        "https://www.erinskidds.com",
        "https://chat.erinskidds.com",
        "https://api.erinskidds.com",
    ]

    # Ollama Settings
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

    # Generation Settings
    MAX_NEW_TOKENS = 300
    TEMPERATURE = 0.3
    NUM_CTX = 4096

    # RAG Settings
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "6"))          # how many chunks to retrieve
    RAG_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.0"))  # minimum similarity score (ChromaDB uses distance)
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    # Sasha's personality system prompt — edit config/system_prompt.txt to update
    _prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
    try:
        with open(_prompt_path, "r", encoding="utf-8") as _f:
            SYSTEM_PROMPT = _f.read().strip()
    except FileNotFoundError:
        SYSTEM_PROMPT = "You are Sasha, an AI assistant representing Erin Skidds."

    # Discord bot settings
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))
    DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
    DISCORD_OWNER_ID = int(os.getenv("DISCORD_OWNER_ID", "0"))
    BACKEND_INTERNAL_URL = os.getenv("BACKEND_INTERNAL_URL", "http://127.0.0.1:8000")

    # Conversation collection
    COLLECTED_CONVERSATIONS_FILE = "./config/collected_conversations.json"

    # Logging
    LOG_LEVEL = "INFO"
    LOG_DIR = "./logs"

    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        for directory in [cls.LOG_DIR, "./config", cls.CHROMA_PERSIST_DIR]:
            os.makedirs(directory, exist_ok=True)


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = "WARNING"


ENV = os.getenv("SASHA_ENV", "development")
if ENV == "production":
    config = ProductionConfig()
else:
    config = DevelopmentConfig()

config.ensure_directories()
