# Sasha-AI Task Tracker

**Goal:** A chatbot embedded in Erin's portfolio that knows and learns about Erin, so visitors can talk to it as if they were talking to her directly.

---

## ✅ What Has Been Done

### Backend (FastAPI + Python)
- [x] FastAPI app scaffolded in `backend/main.py`
- [x] SQLite database with SQLAlchemy (`lib/database.py`) — stores users
- [x] JWT authentication system (`lib/auth.py`, `routes/auth.py`)
  - Default admin user auto-created on startup (`admin` / `admin123`)
  - Register, login, forgot-password routes exist
- [x] `ModelManager` class — rewritten to call local Ollama API (`qwen2.5-coder:7b`) with a system prompt
- [x] `ConversationCollector` — saves every chat turn to `config/collected_conversations.json` for review
- [x] API endpoints: `/chat` (public), `/health`, `/model/status`, `/conversations/stats`
- [x] Ollama system prompt scaffolded in `config/app_config.py` — **needs real Erin details filled in**
- [x] CORS pre-configured for `chat.erinskidds.com` and `api.erinskidds.com`
- [x] `requirements.txt` with all dependencies listed

### Frontend (Next.js + TypeScript + Tailwind)
- [x] Full chat UI with collapsible sidebar, message bubbles, dark/light mode toggle
- [x] Auth flow: Login, Register, Forgot Password pages
- [x] `ProtectedRoute` — redirects unauthenticated users to login
- [x] `AuthContext` — manages JWT token, user state, theme preference
- [x] `ChatInterface` — sends messages to backend `/chat`, displays responses
- [x] Auto-title generation for new chats
- [x] Archive & cleanup of old chats (24-hour expiry)
- [x] Toast notifications
- [x] `UserProfileDropdown` — theme toggle, logout
- [x] API config at `src/config/api.ts` pointing to backend

---

## 🔴 Critical Blockers (Must Fix First)

- [x] **`main.py` references `ChatRequest` but it is never defined** — renamed `MessageRequest` → `ChatRequest` in `main.py`.
- [x] **`lib/model_handler.py` does not exist** — fixed import to `from lib.model_manager import ModelManager` and instantiation to `ModelManager()`.
- [x] **`json` module not imported** — added `import json` to `main.py` (used by the retrain endpoint).
- [ ] **`SECRET_KEY` is hardcoded** in `lib/auth.py` — must be moved to an environment variable before any public exposure.
- [ ] **Default admin password is hardcoded** (`admin123`) — change immediately after first run.

---

## 🟡 High Priority — Core Functionality

### 1. Fix Backend Bugs (above blockers)
- [x] Resolve `ChatRequest` / `MessageRequest` naming mismatch in `main.py`
- [x] Resolve `ModelHandler` vs `ModelManager` import mismatch
- [x] Add missing `import json` to `main.py`
- [x] Update `requirements.txt` to latest versions, drop torch/transformers/datasets/accelerate
- [x] Swap DialoGPT/PyTorch for Ollama API (`lib/model_manager.py` rewritten)
- [x] Remove auth requirement from `/chat` — now fully public for portfolio visitors
- [x] Add conversation history support to `/chat` request
- [ ] Move `SECRET_KEY` to `.env` / environment variable

### 2. Fill In the System Prompt (replaces training data)
No training runs needed — Sasha now uses Ollama with a system prompt.
- [ ] Open `backend/config/app_config.py` and fill in the `SYSTEM_PROMPT` with real details:
  - Your location / region
  - Tech stack (languages, frameworks, tools you use daily)
  - Key projects (name, what it does, tech used)
  - Work experience summary
  - Education
  - Hobbies & interests outside of work
  - Personality / communication style
  - What roles/opportunities you're open to
  - Preferred contact method
- [ ] The more detail you add, the better Sasha sounds — aim for 300–500 words in the prompt

### 3. Install Dependencies & Start the Backend
- [ ] `pip install -r requirements.txt` (from `backend/`)
- [ ] Ensure Ollama is running: `ollama serve` (or it may already be running)
- [ ] Start backend: `python main.py` (from `backend/`)
- [ ] Test: `curl http://localhost:8000/health` — should show `ollama_running: true`

### 4. Verify Frontend ↔ Backend Connection
- [ ] Confirm `src/config/api.ts` points to `http://localhost:8000`
- [ ] Start frontend: `npm run dev` (from `frontend/`)
- [ ] Send a test message — confirm Sasha responds with Ollama (not a canned fallback)
- [ ] Verify conversation history is passed correctly (multi-turn chat works)

---

## 🟠 Medium Priority — Portfolio Integration

### 5. Make the Chat Public-Facing (No Login Required for Visitors)
- [x] Removed `Depends(get_current_user_dependency)` from `/chat` — now fully public
- [ ] Update frontend to skip login and go straight to chat for portfolio visitors (currently shows login page by default)

### 6. Embed in Portfolio
- [x] Method decided: **(B) Floating chat bubble widget** in the portfolio repo (see `.tasks/EMBED-WIDGET.md`)
- [x] Fallback: link to `chat.erinskidds.com` for full-screen experience
- [ ] Implement the widget in `portfolio-next/src/components/SashaWidget.tsx` (code is in `EMBED-WIDGET.md`)
- [ ] Add widget to `portfolio-next/src/app/layout.tsx`
- [ ] Add `NEXT_PUBLIC_SASHA_API_URL` env var to portfolio
- [ ] Update frontend to skip login and go straight to chat for portfolio visitors (currently shows login page by default)
- [ ] Remove the Register page from public view (or hide it) — visitors shouldn't need to create accounts

### 7. Personality & Context Improvements
- [x] System prompt added to every Ollama request — model always knows it's playing Erin
- [x] Switched from fine-tuned DialoGPT to local Ollama (`qwen2.5-coder:7b`) with a system prompt — no GPU training needed
- [x] Conversation history passed on every `/chat` request — multi-turn context works

---

## 🟢 Lower Priority — Polish & Reliability

### 8. Environment & Security
- [ ] Create a `.env` file in `backend/` with:
  ```
  SECRET_KEY=<random 32+ char string>
  ADMIN_PASSWORD=<strong password>
  SASHA_ENV=production
  ```
- [ ] Load `SECRET_KEY` from env in `lib/auth.py`
- [ ] Add `.env` to `.gitignore` (already present but verify)

### 9. Conversation Persistence
- [ ] Currently chats are stored in-memory / local browser storage on the frontend
- [x] Conversation history is passed to `/chat` on each request — model has full session context
- [ ] For a portfolio bot, consider storing nothing (stateless per session) — visitors don't need persistent history

### 10. UI Tweaks for Portfolio
- [ ] Update the chat header/branding to say "Chat with Sasha" or "Ask Erin's AI"
- [ ] Add Erin's avatar/photo as the bot icon instead of the generic "S" placeholder
- [ ] Add suggested starter questions: "What's your tech stack?", "Tell me about your projects", etc.
- [ ] Ensure mobile responsiveness is solid

### 11. Auto-Retraining Pipeline
- [ ] Once live, run `python scripts/start_auto_retrain.py` to enable automatic retraining as visitors chat
- [ ] Review collected conversations periodically and add good ones to `training_data.json`
- [ ] Set `MIN_CONVERSATIONS_FOR_RETRAIN` appropriately in `config/app_config.py`

---

## 📋 Recommended Order of Attack

1. ~~Fix the two critical backend bugs~~ ✅
2. ~~Swap DialoGPT for Ollama~~ ✅
3. ~~Make `/chat` public~~ ✅
4. **Fill in `SYSTEM_PROMPT` in `backend/config/app_config.py`** with real Erin details ← YOU ARE HERE
5. `pip install -r requirements.txt` then `python main.py` — verify `ollama_running: true`
6. Test end-to-end locally (frontend + backend + Ollama all running)
7. Implement the chat widget in `portfolio-next/` (see `EMBED-WIDGET.md`)
8. Set up hosting (see `HOSTING.md`)
9. Move `SECRET_KEY` to `.env` before going public
