"""
Configuration settings for Sasha AI
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

    # Generation Settings
    MAX_NEW_TOKENS = 150
    TEMPERATURE = 0.3

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
    # Internal URL the Discord bot uses to call the FastAPI backend
    BACKEND_INTERNAL_URL = os.getenv("BACKEND_INTERNAL_URL", "http://127.0.0.1:8000")

    # Conversation collection (for reviewing what people ask)
    COLLECTED_CONVERSATIONS_FILE = "./config/collected_conversations.json"

    # Logging
    LOG_LEVEL = "INFO"
    LOG_DIR = "./logs"

    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        for directory in [cls.LOG_DIR, "./config"]:
            os.makedirs(directory, exist_ok=True)


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = "WARNING"


# Select config based on environment
ENV = os.getenv("SASHA_ENV", "development")
if ENV == "production":
    config = ProductionConfig()
else:
    config = DevelopmentConfig()

# Ensure directories exist
config.ensure_directories()
