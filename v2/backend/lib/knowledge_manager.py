"""
Knowledge Manager for Sasha AI v2

Builds the base system prompt and manages RAG index synchronization.
When knowledge entries change, the vector store is updated incrementally
so retrieval stays in sync.
"""

import logging
import os
from sqlalchemy.orm import Session
from lib.database import Knowledge, SessionLocal
from config.app_config import config

logger = logging.getLogger("sasha.knowledge")

PROMPT_HEADER = """You are Sasha, an AI assistant created to help visitors learn professional facts about Erin Skidds.
You speak in third person about Erin — you are NOT Erin, you are an assistant who knows her well.
Use "she", "her", "Erin" when referring to her. Never say "I" as if you are Erin.
Be conversational, warm, and direct. Keep answers concise — this is a portfolio chat widget, not an essay.
If you genuinely don't know something specific about Erin, say so naturally rather than making things up.
IMPORTANT: Only reference technologies, companies, places, and facts listed in the retrieved context below. Do not invent or add anything not mentioned there unless the question is completely off-topic (e.g. math, history, science).
IMPORTANT: Do not answer personal questions like age, marital status, gender, or birthday. Reply: "I do not have permission to answer personal non-work/education related questions. Please ask something else."

"""


def build_base_system_prompt() -> str:
    """
    Return the instruction header only — knowledge facts are injected
    per-query via RAG retrieval, not hardcoded into every prompt.
    """
    return PROMPT_HEADER


def build_full_system_prompt_from_db(db: Session) -> str:
    """
    Fallback: build a complete static prompt from all active DB entries.
    Used when RAG is unavailable (e.g. Ollama embed model missing).
    """
    entries = (
        db.query(Knowledge)
        .filter(Knowledge.is_active == True)
        .order_by(Knowledge.sort_order, Knowledge.category, Knowledge.id)
        .all()
    )

    if not entries:
        return config.SYSTEM_PROMPT

    sections: dict[str, list[str]] = {}
    for entry in entries:
        sections.setdefault(entry.category, []).append(entry.content)

    body_parts = []
    for category, items in sections.items():
        body_parts.append(f"{category.upper()}:")
        for item in items:
            body_parts.append(f"- {item}")
        body_parts.append("")

    return PROMPT_HEADER + "Here is everything you know about Erin:\n\n" + "\n".join(body_parts)


_cached_fallback_prompt: str | None = None


def get_fallback_prompt() -> str:
    """Full static prompt for when RAG is unavailable. Cached."""
    global _cached_fallback_prompt
    if _cached_fallback_prompt is None:
        db = SessionLocal()
        try:
            _cached_fallback_prompt = build_full_system_prompt_from_db(db)
        finally:
            db.close()
    return _cached_fallback_prompt


def invalidate_prompt_cache() -> None:
    global _cached_fallback_prompt
    _cached_fallback_prompt = None


# ── RAG sync helpers ──────────────────────────────────────────────────────────

def sync_entry_to_rag(entry_id: int, category: str, content: str, is_active: bool) -> None:
    """
    Upsert or remove one knowledge entry from the RAG vector store.
    Import is deferred to avoid circular imports at module load.
    """
    try:
        from lib.rag_engine import rag_engine
        if is_active:
            rag_engine.upsert_entry(entry_id, category, content)
        else:
            rag_engine.delete_entry(entry_id)
    except Exception as e:
        logger.warning(f"RAG sync skipped for entry {entry_id}: {e}")


def rebuild_rag_index(db: Session) -> int:
    """Rebuild the full RAG index from all active knowledge entries."""
    try:
        from lib.rag_engine import rag_engine
        entries = (
            db.query(Knowledge)
            .filter(Knowledge.is_active == True)
            .order_by(Knowledge.id)
            .all()
        )
        data = [{"id": e.id, "category": e.category, "content": e.content} for e in entries]
        return rag_engine.rebuild_index(data)
    except Exception as e:
        logger.warning(f"RAG index rebuild failed: {e}")
        return 0


# ── Seed from txt ─────────────────────────────────────────────────────────────

def seed_from_txt(db: Session) -> int:
    """
    One-time seed: parse system_prompt.txt into knowledge rows.
    Only runs if the knowledge table is empty.
    """
    existing = db.query(Knowledge).count()
    if existing > 0:
        return 0

    prompt_path = os.path.join(os.path.dirname(__file__), "..", "config", "system_prompt.txt")
    if not os.path.exists(prompt_path):
        return 0

    with open(prompt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_category = "GENERAL"
    sort_order = 0
    inserted = 0

    for line in lines:
        line = line.rstrip()
        if not line:
            continue
        if line.endswith(":") and line == line.upper() and len(line) < 60:
            current_category = line.rstrip(":").strip()
            continue
        if (
            line.startswith("You are")
            or line.startswith("Use ")
            or line.startswith("Be ")
            or line.startswith("If you")
            or line.startswith("IMPORTANT")
            or "Here is everything" in line
        ):
            continue
        content = line.lstrip("- ").strip()
        if not content:
            continue

        db.add(
            Knowledge(
                category=current_category,
                content=content,
                is_active=True,
                sort_order=sort_order,
            )
        )
        sort_order += 1
        inserted += 1

    db.commit()
    return inserted
