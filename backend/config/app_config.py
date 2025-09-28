"""
Configuration settings for Sasha AI
"""

import os
from typing import Optional

class Config:
    # API Settings
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    CORS_ORIGINS = [
        "http://localhost:*",  # For local development
        "https://chat.erinskidds.com",  # Your deployed frontend
        "https://*.erinskidds.com",  # Allow any ErinSkidds.com subdomain
        "https://api.erinskidds.com"  # Cloudflare Tunnel endpoint
    ]
    
    # Model Settings
    MODEL_DIR = "./models/sasha_model"
    MODEL_BACKUP_DIR = "./models/backups"
    DEFAULT_MODEL_NAME = "microsoft/DialoGPT-medium"
    
    # Training Settings
    TRAINING_DATA_FILE = "./config/training_data.json"
    COLLECTED_CONVERSATIONS_FILE = "./config/collected_conversations.json"
    TRAINING_OUTPUT_DIR = "./models/sasha_model"
    
    # Training Parameters
    TRAINING_EPOCHS = 3
    BATCH_SIZE = 2
    LEARNING_RATE = 5e-5
    MAX_LENGTH = 512
    
    # Auto-retraining Settings
    MIN_CONVERSATIONS_FOR_RETRAIN = 20
    RETRAIN_INTERVAL_HOURS = 6
    BACKUP_MODELS = True
    
    # Generation Settings
    MAX_NEW_TOKENS = 100
    TEMPERATURE = 0.7
    DO_SAMPLE = True
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_DIR = "./logs"
    
    @classmethod
    def get_model_path(cls) -> str:
        """Get the current model path"""
        return cls.MODEL_DIR
    
    @classmethod
    def get_backup_path(cls, timestamp: str) -> str:
        """Get backup path with timestamp"""
        return f"{cls.MODEL_BACKUP_DIR}/sasha_model_backup_{timestamp}"
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        directories = [
            cls.MODEL_DIR,
            cls.MODEL_BACKUP_DIR,
            cls.LOG_DIR,
            "./config"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

# Environment-specific configs
class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = "WARNING"
    MIN_CONVERSATIONS_FOR_RETRAIN = 100  # More conservative in production

# Select config based on environment
ENV = os.getenv("SASHA_ENV", "development")
if ENV == "production":
    config = ProductionConfig()
else:
    config = DevelopmentConfig()

# Ensure directories exist
config.ensure_directories()
