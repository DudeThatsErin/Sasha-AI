# Sasha AI v2

RAG-powered rebuild of Sasha AI. Uses ChromaDB for vector search and Ollama for embeddings and generation. The frontend is the same v1 frontend - only the backend changed.

## How it works

```
User message
    |
    v
FastAPI (/chat)
    |
    |-- teach intent detected -> PendingKnowledge (SQLite) -> Discord approval
    |
    v
RAG Engine
    |
    |-- embed query via Ollama (nomic-embed-text)
    |-- cosine similarity search in ChromaDB
    |-- retrieve top-K relevant knowledge chunks
    v
inject chunks into system prompt -> Ollama (qwen2.5-coder:7b) -> response
```

---

## What changed from v1

| Feature | v1 | v2 |
|---|---|---|
| Knowledge retrieval | full prompt injection (all facts, every query) | RAG: only relevant chunks per query |
| Vector store | none | ChromaDB (persistent, cosine similarity) |
| Embeddings | none | `nomic-embed-text` via Ollama |
| Context usage | high (everything always in context) | low (top-6 chunks only) |
| Index sync | N/A | automatic on CRUD + approve |
| Discord commands | 7 | 9 (adds `/knowledge-rebuild`, `/rag-status`) |
| Fallback | static prompt file | full static prompt if embed model unavailable |

---

## Prerequisites

You need both Ollama models pulled:

```powershell
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
```

---

## Setup

```powershell
cd f:\repos\Sasha-AI\v2\backend

# copy and fill in your env vars
Copy-Item .env.example .env

# install dependencies
pip install -r requirements.txt

# run the backend (port 8000)
python main.py

# run the Discord bot in a separate process
python discord_bot.py
```

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | LLM for generation |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | embedding model for RAG |
| `RAG_TOP_K` | `6` | number of chunks to retrieve per query |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | where ChromaDB stores its index |
| `ADMIN_PASSWORD` | `admin123` | change this |
| `SECRET_KEY` | dev fallback | JWT secret, set a strong random value in production |

---

## New API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/rag/status` | GET | vector store stats |
| `/rag/test` | POST `{query}` | test retrieval for a query |
| `/knowledge/rebuild-index` | POST | force a full RAG index rebuild |

---

## RAG index sync

The index stays in sync automatically:
- On startup - full rebuild from all active knowledge entries
- On `POST /knowledge` - new entry gets embedded and upserted
- On `PUT /knowledge/{id}` - entry re-embedded, or removed from the index if disabled
- On `DELETE /knowledge/{id}` - entry removed from the vector store
- On pending approval - approved entry gets embedded right away

To rebuild manually:
- `POST /knowledge/rebuild-index`
- Discord `/knowledge-rebuild` command

---

## Fallback mode

If `nomic-embed-text` is not available in Ollama, the backend falls back to injecting the full static knowledge prompt into every request. This is the same as v1 behavior. You can check RAG status at `GET /rag/status`.

---

## Migrating from v1

1. Copy your existing `sasha_ai.db` to `v2/backend/sasha_ai.db`
2. Start the backend - the RAG index builds automatically on first startup
3. No schema changes, the SQLite tables are identical

The v1 frontend works with the v2 backend as-is. No frontend changes needed.

---

## Switching the NSSM services

When you're ready to replace v1:

```
SashaBackend  -> change cwd to f:\repos\Sasha-AI\v2\backend
SashaDiscordBot -> change script to f:\repos\Sasha-AI\v2\backend\discord_bot.py
```

The `SashaFrontend` service stays the same since we're reusing the v1 frontend.
