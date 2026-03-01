"""
Sasha AI v2 - FastAPI Backend
RAG-powered knowledge retrieval via ChromaDB + Ollama embeddings
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import logging
import logging.handlers
import os
import httpx

from config.app_config import config
from lib.model_manager import ModelManager
from lib.database import init_database, get_db, Knowledge, PendingKnowledge, engine
from lib.auth import create_default_admin
from lib.conversation_collector import collector
from lib.knowledge_manager import (
    seed_from_txt,
    invalidate_prompt_cache,
    sync_entry_to_rag,
    rebuild_rag_index,
)

from sqlalchemy.orm import sessionmaker, Session
from typing import Optional as Opt

# ── Logging ──────────────────────────────────────────────────────────────────

_log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(_log_dir, exist_ok=True)

_formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_info_handler = logging.handlers.RotatingFileHandler(
    os.path.join(_log_dir, "sasha_api.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
_info_handler.setLevel(logging.INFO)
_info_handler.setFormatter(_formatter)

_err_handler = logging.handlers.RotatingFileHandler(
    os.path.join(_log_dir, "sasha_api_err.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
_err_handler.setLevel(logging.WARNING)
_err_handler.setFormatter(_formatter)

logging.root.setLevel(logging.INFO)
logging.root.addHandler(_info_handler)
logging.root.addHandler(_err_handler)

logger = logging.getLogger("sasha.api")

# ── App setup ────────────────────────────────────────────────────────────────

app = FastAPI(title="Sasha AI Bot", version="2.0.0")

init_database()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
_startup_db = SessionLocal()
try:
    create_default_admin(_startup_db)
finally:
    _startup_db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic models ──────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    chat_id: str
    history: Optional[List[ChatMessage]] = []


class MessageResponse(BaseModel):
    response: str
    chat_id: str


class KnowledgeCreate(BaseModel):
    category: str
    content: str
    sort_order: int = 0


class KnowledgeUpdate(BaseModel):
    category: Opt[str] = None
    content: Opt[str] = None
    is_active: Opt[bool] = None
    sort_order: Opt[int] = None


# ── Model manager ────────────────────────────────────────────────────────────

model_manager = ModelManager()

# ── Startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Sasha AI v2...")
    model_manager.load_model()

    seed_db = SessionLocal()
    try:
        inserted = seed_from_txt(seed_db)
        if inserted:
            logger.info(f"Seeded {inserted} knowledge entries from system_prompt.txt")
        else:
            logger.info("Knowledge DB already populated — skipping seed")
    finally:
        seed_db.close()

    # Build RAG index from all active knowledge entries
    rag_db = SessionLocal()
    try:
        count = rebuild_rag_index(rag_db)
        if count:
            logger.info(f"RAG index built with {count} entries.")
        else:
            logger.info("RAG index empty or embed model unavailable — using fallback prompt.")
    finally:
        rag_db.close()

    logger.info("Sasha AI v2 ready!")


# ── Knowledge endpoints ──────────────────────────────────────────────────────

@app.get("/knowledge")
async def list_knowledge(db: Session = Depends(get_db)):
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
    entry = Knowledge(category=body.category, content=body.content, sort_order=body.sort_order)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    invalidate_prompt_cache()
    # Sync new entry into vector store
    sync_entry_to_rag(entry.id, entry.category, entry.content, is_active=True)
    return {"id": entry.id, "category": entry.category, "content": entry.content}


@app.put("/knowledge/{entry_id}")
async def update_knowledge(entry_id: int, body: KnowledgeUpdate, db: Session = Depends(get_db)):
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
    # Sync updated entry into vector store (upsert or delete if now inactive)
    sync_entry_to_rag(entry.id, entry.category, entry.content, is_active=entry.is_active)
    return {
        "id": entry.id,
        "category": entry.category,
        "content": entry.content,
        "is_active": entry.is_active,
    }


@app.delete("/knowledge/{entry_id}")
async def delete_knowledge(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(Knowledge).filter(Knowledge.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    invalidate_prompt_cache()
    # Remove from vector store
    from lib.rag_engine import rag_engine
    rag_engine.delete_entry(entry_id)
    return {"message": "Deleted"}


@app.post("/knowledge/rebuild-index")
async def rebuild_knowledge_index(db: Session = Depends(get_db)):
    """Force a full rebuild of the RAG vector index."""
    count = rebuild_rag_index(db)
    invalidate_prompt_cache()
    return {"message": f"RAG index rebuilt with {count} entries.", "count": count}


# ── RAG status endpoint ──────────────────────────────────────────────────────

@app.get("/rag/status")
async def rag_status():
    """Return RAG vector store statistics."""
    try:
        from lib.rag_engine import rag_engine
        count = rag_engine.get_index_count()
        return {
            "rag_enabled": model_manager._rag_available,
            "embed_model": config.OLLAMA_EMBED_MODEL,
            "chroma_persist_dir": config.CHROMA_PERSIST_DIR,
            "indexed_entries": count,
            "top_k": config.RAG_TOP_K,
        }
    except Exception as e:
        return {"rag_enabled": False, "error": str(e)}


@app.post("/rag/test")
async def rag_test(body: dict):
    """Test RAG retrieval for a given query (admin use)."""
    query = body.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="query field required")
    try:
        from lib.rag_engine import rag_engine
        chunks = rag_engine.retrieve(query)
        return {"query": query, "chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Auth routes ──────────────────────────────────────────────────────────────

from routes.auth import router as auth_router
app.include_router(auth_router)


# ── Root ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    stats = collector.get_conversation_stats()
    return {
        "message": "Sasha AI v2 is running!",
        "version": "2.0.0",
        "rag": "enabled" if model_manager._rag_available else "disabled (fallback mode)",
        "collected_conversations": stats["total_conversations"],
        "model_status": model_manager.get_status(),
    }


# ── Teach intent detection ────────────────────────────────────────────────────

TEACH_TRIGGERS = [
    "remember that", "remember erin", "remember she", "remember her",
    "learn that", "know that", "note that",
    "add to your knowledge", "update your knowledge", "teach you",
    "you should know", "did you know that", "i want you to know",
    "can you remember", "please remember", "store this",
]

TEACH_STARTS_WITH = [
    "erin is ", "erin has ", "erin was ", "erin likes ", "erin loves ",
    "erin works ", "erin lives ", "erin went ", "erin studied ",
    "remember ",
]


def _detect_teach_intent(message: str) -> str | None:
    lower = message.lower().strip()
    if lower.endswith("?"):
        return None
    for trigger in TEACH_TRIGGERS:
        if trigger in lower:
            idx = lower.index(trigger) + len(trigger)
            fact = message[idx:].strip().lstrip(":,- ").strip()
            if len(fact) > 3:
                return fact
    for trigger in TEACH_STARTS_WITH:
        if lower.startswith(trigger):
            fact = message[len(trigger):].strip().lstrip(":,- ").strip() if trigger == "remember " else message.strip()
            if len(fact) > 3:
                return fact
    return None


# ── Discord notify helpers ────────────────────────────────────────────────────

DISCORD_NOTIFY_URL = os.getenv("DISCORD_NOTIFY_URL", "http://127.0.0.1:8001/notify-pending")
DISCORD_WIDGET_URL = os.getenv("DISCORD_WIDGET_URL", "http://127.0.0.1:8001/notify-widget")


async def _notify_discord(pending_id: int, content: str) -> Opt[str]:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(DISCORD_NOTIFY_URL, json={"pending_id": pending_id, "content": content})
            if r.status_code == 200:
                return r.json().get("discord_message_id")
    except Exception as e:
        logger.warning(f"Discord notify failed (non-fatal): {e}")
    return None


async def _notify_discord_widget(message: str, chat_id: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(DISCORD_WIDGET_URL, json={"message": message, "chat_id": chat_id})
    except Exception as e:
        logger.warning(f"Discord widget notify failed (non-fatal): {e}")


# ── MISC question storage ────────────────────────────────────────────────────

_MISC_SKIP_KEYWORDS = [
    "boston celtics", "nba", "nfl", "nhl", "mlb", "weather", "stock",
    "recipe", "movie", "song", "capital of", "president of", "who won",
    "what is the", "how do you", "how does", "define ", "meaning of",
    "translate", "calculate", "math", "history of", "when was",
]


def _is_erin_related(question: str) -> bool:
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
        logger.warning(f"Failed to store misc question (non-fatal): {e}")


# ── Chat endpoint ────────────────────────────────────────────────────────────

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Public chat endpoint — uses RAG to retrieve relevant knowledge per query."""
    try:
        proposed_fact = _detect_teach_intent(request.message)
        if proposed_fact:
            pending = PendingKnowledge(
                category="GENERAL",
                content=proposed_fact,
                proposed_by_chat_id=request.chat_id,
                status="pending",
            )
            db.add(pending)
            db.commit()
            db.refresh(pending)

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

        collector.add_conversation(
            user_message=request.message,
            assistant_response=bot_response,
            chat_id=request.chat_id,
        )

        _store_misc_question(request.message, bot_response, db)

        await _notify_discord_widget(request.message, request.chat_id or "unknown")

        return MessageResponse(response=bot_response, chat_id=request.chat_id)
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Pending knowledge endpoints ───────────────────────────────────────────────

@app.get("/pending-knowledge")
async def list_pending(db: Session = Depends(get_db)):
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
    from datetime import datetime as dt
    pending = db.query(PendingKnowledge).filter(PendingKnowledge.id == entry_id).first()
    if not pending:
        raise HTTPException(status_code=404, detail="Pending entry not found")
    if pending.status != "pending":
        raise HTTPException(status_code=400, detail=f"Entry already {pending.status}")

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
    db.refresh(entry)
    invalidate_prompt_cache()
    # Index approved entry in RAG
    sync_entry_to_rag(entry.id, entry.category, entry.content, is_active=True)
    return {"message": "Approved and added to knowledge base", "knowledge_id": entry.id}


@app.post("/pending-knowledge/{entry_id}/deny")
async def deny_pending(entry_id: int, db: Session = Depends(get_db)):
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
    return {"discord_message_id": None}


# ── Conversation endpoints ───────────────────────────────────────────────────

@app.get("/conversations/stats")
async def get_conversation_stats():
    return collector.get_conversation_stats()


@app.delete("/conversations")
async def clear_conversations():
    collector.clear_conversations()
    return {"message": "All conversations cleared"}


# ── Model endpoints ──────────────────────────────────────────────────────────

@app.get("/model/status")
async def model_status():
    return {
        "model": model_manager.get_status(),
        "conversations": collector.get_conversation_stats(),
    }


@app.post("/model/reload")
async def reload_model(db: Session = Depends(get_db)):
    model_manager.load_model()
    # Re-check RAG availability and rebuild if needed
    if model_manager._rag_available:
        count = rebuild_rag_index(db)
        logger.info(f"RAG index rebuilt after model reload: {count} entries")
    return {"message": "Model reloaded", "status": model_manager.get_status()}


@app.get("/health")
async def health_check():
    from lib.rag_engine import rag_engine
    return {
        "status": "healthy",
        "version": "2.0.0",
        "conversations_collected": len(collector.conversations),
        "ollama": model_manager.get_status(),
        "rag_index_size": rag_engine.get_index_count(),
    }


if __name__ == "__main__":
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)
