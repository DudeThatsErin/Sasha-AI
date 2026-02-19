# Sasha-AI

**Sasha** is a personal AI chatbot built to represent Erin Skidds. It lives on Erin's portfolio so that visitors can have a conversation with it as if they were talking directly to Erin — asking about her background, projects, tech stack, personality, and anything else they'd want to know before reaching out.

---

## What It Does

- **Talks like Erin** — trained on real Q&A conversation pairs written in Erin's voice, covering her experience, opinions, hobbies, and work
- **Learns over time** — every conversation is collected and used to automatically retrain the model, so Sasha gets better the more people interact with it
- **Lives on the portfolio** — embedded at `chat.erinskidds.com`, accessible to anyone visiting Erin's portfolio without needing an account
- **Runs locally** — the backend runs on Erin's home PC and is exposed to the internet via a Cloudflare Tunnel (no cloud GPU costs)

---

## Architecture

```
frontend/          Next.js 14 + TypeScript + Tailwind CSS
                   Full chat UI with sidebar, dark mode, auth flow

backend/           Python + FastAPI
                   Model inference, training pipeline, conversation collection
                   SQLite database for user management
                   DialoGPT-medium fine-tuned on Erin-specific training data
```

**Public URLs (when live):**
- Frontend: `https://chat.erinskidds.com`
- Backend API: `https://api.erinskidds.com`

---

## Project Status

| Area | Status |
|------|--------|
| Frontend UI (chat, auth, sidebar, dark mode) | ✅ Complete |
| Backend API (FastAPI, auth, endpoints) | ✅ Scaffolded — has 2 bugs to fix (see `.tasks/TODO.md`) |
| Training pipeline (SashaTrainer, auto-retrain) | ✅ Built |
| Erin-specific training data | ❌ Not written yet — generic placeholder data only |
| Initial model training | ❌ Not run yet |
| Public chat (no login required for visitors) | ❌ Currently requires auth — needs to be removed for portfolio use |
| Hosting / Cloudflare Tunnel | ❌ Not configured yet |
| Portfolio embed | ❌ Not done yet |

---

## Getting Started (Local Development)

### Backend
```powershell
cd backend
pip install -r requirements.txt
python main.py
# API runs at http://localhost:8000
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
# UI runs at http://localhost:3000
```

---

## Task Tracking

See `.tasks/` for detailed task lists:

- **`.tasks/TODO.md`** — Full breakdown of what's done, what's broken, and what needs to happen next (in priority order)
- **`.tasks/HOSTING.md`** — Step-by-step guide to exposing the local backend to the internet via Cloudflare Tunnel and deploying the frontend to Vercel

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI, Uvicorn |
| AI Model | DialoGPT-medium (Hugging Face Transformers) |
| Database | SQLite via SQLAlchemy |
| Auth | JWT (python-jose + bcrypt) |
| Tunnel | Cloudflare Tunnel (cloudflared) |
| Hosting | Vercel (frontend) + Home PC (backend) |
