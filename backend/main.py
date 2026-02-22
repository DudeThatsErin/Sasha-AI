"""
Sasha AI - FastAPI Backend powered by Ollama
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import logging

from config.app_config import config
from lib.model_manager import ModelManager
from lib.database import init_database
from lib.auth import create_default_admin
from lib.conversation_collector import collector

from sqlalchemy.orm import sessionmaker
from lib.database import engine

app = FastAPI(title="Sasha AI Bot", version="3.0.0")

# Initialize database
init_database()

# Create default admin user
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()
try:
    create_default_admin(db)
finally:
    db.close()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    chat_id: str
    history: Optional[List[ChatMessage]] = []  # conversation history for context

class MessageResponse(BaseModel):
    response: str
    chat_id: str

# Initialize model manager
model_manager = ModelManager()

@app.on_event("startup")
async def startup_event():
    """Check Ollama is reachable on startup"""
    print("Starting Sasha AI Bot...")
    model_manager.load_model()
    print("Sasha AI Bot ready!")

# Include authentication routes
from routes.auth import router as auth_router
app.include_router(auth_router)

@app.get("/")
async def root():
    """Root endpoint with status information"""
    stats = collector.get_conversation_stats()
    return {
        "message": "Sasha AI Bot is running!",
        "version": "3.0.0",
        "collected_conversations": stats["total_conversations"],
        "model_status": model_manager.get_status(),
    }

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Public chat endpoint — no authentication required"""
    try:
        history = [{"role": m.role, "content": m.content} for m in (request.history or [])]
        bot_response = model_manager.generate_response(
            request.message,
            conversation_history=history,
        )

        # Collect conversation for review
        collector.add_conversation(
            user_message=request.message,
            assistant_response=bot_response,
            chat_id=request.chat_id,
        )

        return MessageResponse(response=bot_response, chat_id=request.chat_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === CONVERSATION MANAGEMENT ENDPOINTS ===

@app.get("/conversations/stats")
async def get_conversation_stats():
    """Get statistics about collected conversations"""
    return collector.get_conversation_stats()

@app.delete("/conversations")
async def clear_conversations():
    """Clear all collected conversations"""
    collector.clear_conversations()
    return {"message": "All conversations cleared"}

# === MODEL MANAGEMENT ENDPOINTS ===

@app.get("/model/status")
async def model_status():
    """Get model and conversation status"""
    return {
        "model": model_manager.get_status(),
        "conversations": collector.get_conversation_stats(),
    }

@app.post("/model/reload")
async def reload_model():
    """Re-check Ollama availability"""
    model_manager.load_model()
    return {"message": "Model reloaded", "status": model_manager.get_status()}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "conversations_collected": len(collector.conversations),
        "ollama": model_manager.get_status(),
    }

if __name__ == "__main__":
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)