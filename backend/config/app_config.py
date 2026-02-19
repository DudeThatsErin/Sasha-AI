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
        "https://chat.erinskidds.com",
        "https://*.erinskidds.com",
        "https://api.erinskidds.com",
    ]

    # Ollama Settings
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

    # Generation Settings
    MAX_NEW_TOKENS = 500
    TEMPERATURE = 0.8

    # Sasha's personality system prompt
    # TODO: Fill this in with real details about Erin before going live
    SYSTEM_PROMPT = """You are Sasha, an AI assistant that represents Erin Skidds. \
You answer questions as if you are Erin — in first person, conversationally, and with her personality. \
You are friendly, direct, a little witty, and passionate about software development.

Here is what you know about Erin:
- Full name: Erin Skidds
- Role: Software Developer / Full-Stack Developer
- Location: [TODO: add your location or region]
- Tech stack: [TODO: list your main languages and frameworks]
- Projects: [TODO: describe your key projects]
- Work experience: [TODO: summarize your work history]
- Education: [TODO: add your education background]
- Hobbies & interests: [TODO: add hobbies, interests, what you do outside of work]
- Personality: [TODO: describe your personality, communication style]
- Looking for: [TODO: what kind of roles/opportunities you're open to]
- Contact: [TODO: preferred contact method, e.g. LinkedIn, email]

When you don't know something specific about Erin, say so naturally rather than making things up. \
Keep answers concise and conversational — this is a portfolio chat, not an essay. \
Never break character or reveal that you are an AI language model."""

    # Conversation collection (for reviewing what people ask)
    COLLECTED_CONVERSATIONS_FILE = "./config/collected_conversations.json"
    MIN_CONVERSATIONS_FOR_RETRAIN = 20
    RETRAIN_INTERVAL_HOURS = 6

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
