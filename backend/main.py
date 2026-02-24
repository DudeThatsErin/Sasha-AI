"""
Sasha AI - FastAPI Backend powered by Ollama
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import logging
import os
import httpx

from config.app_config import config
from lib.model_manager import ModelManager
from lib.database import init_database, get_db, Knowledge, PendingKnowledge
from lib.auth import create_default_admin
from lib.conversation_collector import collector
from lib.knowledge_manager import seed_from_txt, invalidate_prompt_cache

from sqlalchemy.orm import sessionmaker, Session
from lib.database import engine
from fastapi import Depends
from typing import Optional as Opt

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

class KnowledgeCreate(BaseModel):
    category: str
    content: str
    sort_order: int = 0

class KnowledgeUpdate(BaseModel):
    category: Opt[str] = None
    content: Opt[str] = None
    is_active: Opt[bool] = None
    sort_order: Opt[int] = None


@app.on_event("startup")
async def startup_event():
    """Check Ollama is reachable on startup and seed knowledge DB"""
    print("Starting Sasha AI Bot...")
    model_manager.load_model()
    seed_db = SessionLocal()
    try:
        inserted = seed_from_txt(seed_db)
        if inserted:
            print(f"Seeded {inserted} knowledge entries from system_prompt.txt")
        else:
            print("Knowledge DB already populated — skipping seed")
    finally:
        seed_db.close()
    print("Sasha AI Bot ready!")


# === KNOWLEDGE MANAGEMENT ENDPOINTS ===

@app.get("/knowledge")
async def list_knowledge(db: Session = Depends(get_db)):
    """List all knowledge entries"""
    entries = db.query(Knowledge).order_by(Knowledge.sort_order, Knowledge.category, Knowledge.id).all()
    return [
        {
            "id": e.id,
            "category": e.category,
            "content": e.content,
            "is_active": e.is_active,
            "sort_order": e.sort_order,
            "created_at": e.created_at,
            "updated_at": e.updated_at,
        }
        for e in entries
    ]

@app.post("/knowledge", status_code=201)
async def create_knowledge(body: KnowledgeCreate, db: Session = Depends(get_db)):
    """Add a new knowledge entry"""
    entry = Knowledge(category=body.category, content=body.content, sort_order=body.sort_order)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    invalidate_prompt_cache()
    return {"id": entry.id, "category": entry.category, "content": entry.content}

@app.put("/knowledge/{entry_id}")
async def update_knowledge(entry_id: int, body: KnowledgeUpdate, db: Session = Depends(get_db)):
    """Update a knowledge entry"""
    entry = db.query(Knowledge).filter(Knowledge.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if body.category is not None:
        entry.category = body.category
    if body.content is not None:
        entry.content = body.content
    if body.is_active is not None:
        entry.is_active = body.is_active
    if body.sort_order is not None:
        entry.sort_order = body.sort_order
    db.commit()
    db.refresh(entry)
    invalidate_prompt_cache()
    return {"id": entry.id, "category": entry.category, "content": entry.content, "is_active": entry.is_active}

@app.delete("/knowledge/{entry_id}")
async def delete_knowledge(entry_id: int, db: Session = Depends(get_db)):
    """Delete a knowledge entry"""
    entry = db.query(Knowledge).filter(Knowledge.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    invalidate_prompt_cache()
    return {"message": "Deleted"}

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

TEACH_TRIGGERS = [
    "remember that", "remember erin", "remember she", "remember her",
    "learn that", "know that", "note that",
    "add to your knowledge", "update your knowledge", "teach you",
    "you should know", "did you know that", "i want you to know",
    "can you remember", "please remember", "store this",
]

# These only trigger when the message STARTS with them (user stating a fact, not asking)
TEACH_STARTS_WITH = [
    "erin is ", "erin has ", "erin was ", "erin likes ", "erin loves ",
    "erin works ", "erin lives ", "erin went ", "erin studied ",
    "remember ",
]

def _detect_teach_intent(message: str) -> str | None:
    """Return the proposed fact if the message looks like a teach request, else None."""
    lower = message.lower().strip()

    # Reject questions
    if lower.endswith("?"):
        return None

    # Check phrase-anywhere triggers
    for trigger in TEACH_TRIGGERS:
        if trigger in lower:
            idx = lower.index(trigger) + len(trigger)
            fact = message[idx:].strip().lstrip(":,- ").strip()
            if len(fact) > 3:
                return fact

    # Check starts-with triggers (statement of fact)
    for trigger in TEACH_STARTS_WITH:
        if lower.startswith(trigger):
            if trigger == "remember ":
                # "remember X" — fact is everything after "remember "
                fact = message[len(trigger):].strip().lstrip(":,- ").strip()
            else:
                # "erin is X" — whole message is the fact
                fact = message.strip()
            if len(fact) > 3:
                return fact

    return None


DISCORD_NOTIFY_URL = os.getenv("DISCORD_NOTIFY_URL", "http://127.0.0.1:8001/notify-pending")
DISCORD_WIDGET_URL = os.getenv("DISCORD_WIDGET_URL", "http://127.0.0.1:8001/notify-widget")

async def _notify_discord(pending_id: int, content: str) -> Opt[str]:
    """Fire-and-forget HTTP call to the Discord bot's internal notify server."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(
                DISCORD_NOTIFY_URL,
                json={"pending_id": pending_id, "content": content},
            )
            if r.status_code == 200:
                return r.json().get("discord_message_id")
    except Exception as e:
        print(f"Discord notify failed (non-fatal): {e}")
    return None

async def _notify_discord_widget(message: str, chat_id: str) -> None:
    """Notify Discord that someone used the portfolio widget."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                DISCORD_WIDGET_URL,
                json={"message": message, "chat_id": chat_id},
            )
    except Exception as e:
        print(f"Discord widget notify failed (non-fatal): {e}")

_MISC_SKIP_KEYWORDS = [
    "boston celtics", "nba", "nfl", "nhl", "mlb", "weather", "stock",
    "recipe", "movie", "song", "capital of", "president of", "who won",
    "what is the", "how do you", "how does", "define ", "meaning of",
    "translate", "calculate", "math", "history of", "when was",
]

def _is_erin_related(question: str) -> bool:
    """Return True if the question is likely about Erin rather than general knowledge."""
    lower = question.lower()
    for skip in _MISC_SKIP_KEYWORDS:
        if skip in lower:
            return False
    erin_signals = [
        "erin", "you", "your", "she", "her", "sasha",
        "work", "job", "career", "project", "tech", "stack",
        "experience", "skill", "education", "degree", "hire",
        "contact", "reach", "portfolio", "github", "linkedin",
    ]
    return any(s in lower for s in erin_signals)

def _store_misc_question(question: str, answer: str, db: Session) -> None:
    """Store visitor questions about Erin in the MISC category for review."""
    if not _is_erin_related(question):
        return
    try:
        entry = Knowledge(
            category="MISC",
            content=question.strip(),
            is_active=False,
            sort_order=999,
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        print(f"Failed to store misc question (non-fatal): {e}")


@app.post("/chat")
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Public chat endpoint — no authentication required"""
    try:
        # Check for teach intent before calling the model
        proposed_fact = _detect_teach_intent(request.message)
        if proposed_fact:
            # Create a pending entry
            pending = PendingKnowledge(
                category="GENERAL",
                content=proposed_fact,
                proposed_by_chat_id=request.chat_id,
                status="pending",
            )
            db.add(pending)
            db.commit()
            db.refresh(pending)

            # Notify Discord (best-effort)
            discord_msg_id = await _notify_discord(pending.id, proposed_fact)
            if discord_msg_id:
                pending.discord_message_id = discord_msg_id
                db.commit()

            response_text = (
                "That's interesting! Let me ask Erin if it's okay for me to learn that. "
                "She'll review it and I'll know it once she approves it."
            )
            collector.add_conversation(
                user_message=request.message,
                assistant_response=response_text,
                chat_id=request.chat_id,
            )
            return MessageResponse(response=response_text, chat_id=request.chat_id)

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

        # Store question in MISC category so Erin can see what people ask
        _store_misc_question(request.message, bot_response, db)

        # Notify Discord when widget is used (best-effort)
        await _notify_discord_widget(request.message, request.chat_id or "unknown")

        return MessageResponse(response=bot_response, chat_id=request.chat_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === PENDING KNOWLEDGE APPROVAL ENDPOINTS ===

@app.get("/pending-knowledge")
async def list_pending(db: Session = Depends(get_db)):
    """List all pending knowledge entries awaiting approval"""
    entries = db.query(PendingKnowledge).order_by(PendingKnowledge.created_at.desc()).all()
    return [
        {
            "id": e.id,
            "category": e.category,
            "content": e.content,
            "status": e.status,
            "proposed_by_chat_id": e.proposed_by_chat_id,
            "discord_message_id": e.discord_message_id,
            "created_at": e.created_at,
            "reviewed_at": e.reviewed_at,
        }
        for e in entries
    ]

@app.post("/pending-knowledge/{entry_id}/approve")
async def approve_pending(entry_id: int, db: Session = Depends(get_db)):
    """Approve a pending knowledge entry — moves it to the live knowledge table"""
    from datetime import datetime as dt
    pending = db.query(PendingKnowledge).filter(PendingKnowledge.id == entry_id).first()
    if not pending:
        raise HTTPException(status_code=404, detail="Pending entry not found")
    if pending.status != "pending":
        raise HTTPException(status_code=400, detail=f"Entry already {pending.status}")

    # Move to live knowledge
    entry = Knowledge(
        category=pending.category,
        content=pending.content,
        is_active=True,
        sort_order=0,
    )
    db.add(entry)
    pending.status = "approved"
    pending.reviewed_at = dt.utcnow()
    db.commit()
    return {"message": "Approved and added to knowledge base", "knowledge_id": entry.id}

@app.post("/pending-knowledge/{entry_id}/deny")
async def deny_pending(entry_id: int, db: Session = Depends(get_db)):
    """Deny a pending knowledge entry"""
    from datetime import datetime as dt
    pending = db.query(PendingKnowledge).filter(PendingKnowledge.id == entry_id).first()
    if not pending:
        raise HTTPException(status_code=404, detail="Pending entry not found")
    if pending.status != "pending":
        raise HTTPException(status_code=400, detail=f"Entry already {pending.status}")

    pending.status = "denied"
    pending.reviewed_at = dt.utcnow()
    db.commit()
    return {"message": "Denied"}

@app.post("/discord/notify-pending")
async def discord_notify_stub(body: dict):
    """Stub — the Discord bot process intercepts this via its own HTTP server or we call it directly."""
    return {"discord_message_id": None}

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