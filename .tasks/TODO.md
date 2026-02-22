# Sasha-AI Task Tracker

**Goal:** A chatbot embedded in Erin's portfolio that knows about Erin, so visitors can talk to it as if they were talking to her directly.

---

## ✅ Completed

### Backend
- [x] FastAPI app in `backend/main.py`
- [x] SQLite + SQLAlchemy (`lib/database.py`)
- [x] JWT auth (`lib/auth.py`, `routes/auth.py`) — admin user auto-created on startup
- [x] Swapped DialoGPT/PyTorch for local Ollama API — no GPU, no training required
- [x] `ModelManager` calls `qwen2.5-coder:7b` via Ollama with a system prompt
- [x] System prompt moved to `config/system_prompt.txt` — edit that file to update Sasha
- [x] System prompt filled in with real Erin details (work history, tech stack, projects, personality)
- [x] `/chat` is fully public — no auth required for portfolio visitors
- [x] Conversation history passed on every request — multi-turn chat works
- [x] `ConversationCollector` saves every chat turn to `config/collected_conversations.json`
- [x] All dead code removed: `auto_retrainer.py`, `model_trainer.py`, `scripts/`, feedback endpoints
- [x] CORS configured for `chat.erinskidds.com` and `api.erinskidds.com`
- [x] `requirements.txt` up to date

### Portfolio Widget (`portfolio-next`)
- [x] `SashaWidget.tsx` — floating chat bubble, opens panel, sends messages to backend
- [x] Widget wired into `layout.tsx` — appears on every page
- [x] Offline fallback shows clickable LinkedIn + GitHub links
- [x] CSS refactored — single-use classes converted to Tailwind inline, `globals.css` consolidated

---

## � Remaining — Security (Do Before Going Public)

- [ ] **`SECRET_KEY` is hardcoded** in `lib/auth.py` — move to `.env`
- [ ] **Default admin password is `admin123`** — change after first run

To fix `SECRET_KEY`:
1. Create `backend/.env`:
   ```
   SECRET_KEY=<random 32+ char string>
   SASHA_ENV=production
   ```
2. In `lib/auth.py`, replace the hardcoded value with:
   ```python
   SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-fallback")
   ```
3. Confirm `backend/.env` is in `.gitignore`

---

## 🟡 Remaining — Hosting

- [ ] **Set up Cloudflare Tunnel** so `api.erinskidds.com` reaches the local backend
  - See `HOSTING.md` for full steps
  - Once running: `python main.py` + `cloudflared tunnel run sasha-ai-backend`
- [ ] **Add `NEXT_PUBLIC_SASHA_API_URL`** env var to `portfolio-next` pointing to `https://api.erinskidds.com`

---

## 🟢 Optional Polish

- [ ] Add Erin's photo as the Sasha avatar instead of the "S" placeholder
- [ ] Add suggested starter questions to the widget (e.g. "What's your tech stack?")
- [ ] Periodically review `config/collected_conversations.json` to see what visitors are asking

---

## 📋 What's Left (In Order)

1. Move `SECRET_KEY` to `.env` in `lib/auth.py`
2. Change the default admin password
3. Set up Cloudflare Tunnel → `api.erinskidds.com` (see `HOSTING.md`)
4. Add `NEXT_PUBLIC_SASHA_API_URL` to portfolio `.env.local`
5. Test the widget end-to-end against the live backend
