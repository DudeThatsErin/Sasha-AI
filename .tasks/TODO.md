# Sasha-AI Task Tracker

Test

**Goal:** A chatbot embedded in Erin's portfolio that knows about Erin, so visitors can talk to it as if they were talking to her directly. Long-term: replace Ollama with a fully custom-trained AI model.

---

## ✅ Completed

### Backend
- [x] FastAPI app in `backend/main.py`
- [x] SQLite + SQLAlchemy — `Knowledge`, `PendingKnowledge`, `User` tables
- [x] JWT auth — admin user auto-created on startup
- [x] Ollama API integration (`qwen2.5-coder:7b`) via `ModelManager`
- [x] Knowledge base stored in SQLite, built into system prompt dynamically per request
- [x] `system_prompt.txt` seeds the DB on first run only
- [x] `/chat` fully public — no auth required for portfolio visitors
- [x] Multi-turn conversation history passed on every request
- [x] Teach-intent detection — "remember X" / "Erin is X" triggers approval flow
- [x] Pending knowledge queue with Discord approve/deny workflow
- [x] All conversations stored in MISC DB category for review
- [x] CORS configured for `chat.erinskidds.com` and `api.erinskidds.com`
- [x] `.env` / `.env.example` for all secrets and Discord config
- [x] All services running as NSSM Windows services (auto-start on reboot)

### Discord Bot
- [x] `discord_bot.py` — runs as `SashaDiscordBot` NSSM service
- [x] Pings Erin with ✅ Yes / ❌ No buttons when teach-intent is detected
- [x] Notifies Erin in Discord every time the widget is used
- [x] Slash commands: `/knowledge-list`, `/knowledge-add`, `/knowledge-delete`, `/knowledge-toggle`
- [x] Slash commands: `/pending-list`, `/pending-approve`, `/pending-deny`
- [x] `/knowledge-list` truncation links to admin panel

### Frontend (`chat.erinskidds.com`)
- [x] Full chat UI — sidebar, dark/light mode, chat history in localStorage
- [x] Admin panel at `/admin` — Knowledge Base tab + Pending Approval tab with badge count
- [x] Widget import via `?import_chat=<id>` query param
- [x] Offline message with clickable LinkedIn + GitHub links
- [x] Markdown link rendering in messages (`[text](url)` → anchor tags)
- [x] `scrollTop`-based scroll (no `scrollIntoView` document expansion)

### Portfolio Widget (`erinskidds.com`)
- [x] `SashaWidget.tsx` — floating chat bubble on every portfolio page
- [x] Offline fallback with LinkedIn + GitHub links
- [x] Stale/broken offline messages auto-cleaned from localStorage on load
- [x] `SASHA_OFFLINE` sentinel detection for clean offline UX

### Hosting
- [x] Cloudflare Tunnel — `api.erinskidds.com` → local FastAPI
- [x] Cloudflare Tunnel — `chat.erinskidds.com` → local Next.js
- [x] `OllamaService` NSSM service — Ollama auto-starts on reboot

---

## 🟡 In Progress / Short-Term Polish

- [ ] Fix blank space below chat on `chat.erinskidds.com` after messages load
- [ ] Add Erin's photo as the Sasha avatar instead of the "S" placeholder
- [ ] Add suggested starter questions to the widget (e.g. "What's your tech stack?")
- [ ] Review MISC category in admin panel periodically to see what visitors are asking

---

## � Long-Term — Build a Custom AI Model from Scratch

> See `CUSTOM-AI.md` for a full ELI5 guide on how to do this.

The current Sasha uses Ollama (a pre-built model) with a system prompt. The long-term goal is to replace this with a model that is **trained specifically on Erin's data** — her writing style, Q&A pairs, personality, and knowledge.

### Milestones

- [ ] **Phase 1 — Collect training data**
  - Write 200–500 Q&A pairs in Erin's voice covering work, projects, personality, opinions
  - Export all approved knowledge entries from the DB as training examples
  - Save collected conversations from `MISC` category as additional training signal

- [ ] **Phase 2 — Fine-tune a base model**
  - Choose a small open-source base model (e.g. `TinyLlama`, `Phi-3-mini`, `Mistral-7B`)
  - Fine-tune it on the Q&A dataset using `transformers` + `trl` (SFTTrainer)
  - See `CUSTOM-AI.md` for step-by-step instructions

- [ ] **Phase 3 — Evaluate and iterate**
  - Test the fine-tuned model against common questions
  - Compare responses to the Ollama baseline
  - Iterate on training data quality and quantity

- [ ] **Phase 4 — Swap into backend**
  - Replace `ModelManager`'s Ollama API calls with local model inference
  - Keep the same `/chat` endpoint — no frontend changes needed
  - Optionally quantize the model (GGUF/llama.cpp) to reduce memory usage

- [ ] **Phase 5 — Auto-retrain pipeline**
  - When new knowledge is approved via Discord, automatically add it to the training set
  - Schedule periodic fine-tuning runs (weekly/monthly)
  - Version the model so you can roll back if a retrain makes things worse
