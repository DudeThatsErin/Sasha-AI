"""
Knowledge Manager for Sasha AI
Builds the system prompt dynamically from the knowledge database.
Falls back to system_prompt.txt if the DB has no entries.
"""

from sqlalchemy.orm import Session
from lib.database import Knowledge, SessionLocal
from config.app_config import config
import os


PROMPT_HEADER = """You are Sasha, an AI assistant created to help visitors learn professional facts about Erin Skidds.
You speak in third person about Erin — you are NOT Erin, you are an assistant who knows her well.
Use "she", "her", "Erin" when referring to her. Never say "I" as if you are Erin.
Be conversational, warm, and direct. Keep answers concise — this is a portfolio chat widget, not an essay.
If you genuinely don't know something specific about Erin, say so naturally rather than making things up.
IMPORTANT: Only reference technologies, companies, places, and facts explicitly listed below. Do not invent or add anything not mentioned here unless it is completely off-topic like asking math questions or about history or science, etcetera.

Here is everything you know about Erin:
"""


def build_system_prompt_from_db(db: Session) -> str:
    """Build a system prompt string from active knowledge entries, grouped by category."""
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

    return PROMPT_HEADER + "\n".join(body_parts)


_cached_prompt: str | None = None


def get_system_prompt() -> str:
    """Get the current system prompt, preferring DB over flat file. Cached after first load."""
    global _cached_prompt
    if _cached_prompt is None:
        db = SessionLocal()
        try:
            _cached_prompt = build_system_prompt_from_db(db)
        finally:
            db.close()
    return _cached_prompt


def invalidate_prompt_cache() -> None:
    """Call this whenever knowledge entries are added/updated/deleted."""
    global _cached_prompt
    _cached_prompt = None


def seed_from_txt(db: Session) -> int:
    """
    One-time seed: parse system_prompt.txt into knowledge rows.
    Only runs if the knowledge table is empty.
    Returns number of rows inserted.
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
        # Detect category headers like "WORK EXPERIENCE:" or "TECH STACK:"
        if line.endswith(":") and line == line.upper() and len(line) < 60:
            current_category = line.rstrip(":").strip()
            continue
        # Skip the header/instruction lines (before "Here is everything you know")
        if line.startswith("You are") or line.startswith("Use ") or line.startswith("Be ") \
                or line.startswith("If you") or line.startswith("IMPORTANT") \
                or "Here is everything" in line:
            continue
        # Strip bullet prefix
        content = line.lstrip("- ").strip()
        if not content:
            continue

        db.add(Knowledge(
            category=current_category,
            content=content,
            is_active=True,
            sort_order=sort_order,
        ))
        sort_order += 1
        inserted += 1

    db.commit()
    return inserted
