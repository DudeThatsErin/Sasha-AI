# Sasha-AI

**Sasha** is a personal AI chatbot built to represent Erin Skidds. It lives on Erin's portfolio so visitors can ask about her background, projects, tech stack, and experience. Sasha is also a long-term digital heirloom — a way for Erin's future family to learn about her.

---

## What It Does

- **Answers questions about Erin** — powered by a local Ollama model with a dynamic knowledge base stored in SQLite
- **Learns with approval** — when someone tries to teach Sasha something new, it goes into a pending queue and pings Erin on Discord for approval before being added
- **Tracks what people ask** — all conversations are logged so Erin can see what visitors are curious about
- **Managed via Discord** — slash commands let Erin add, edit, enable/disable, and approve knowledge entries directly from Discord
- **Admin UI** — web-based admin panel at `chat.erinskidds.com/admin` for full knowledge base management
- **Runs locally** — backend runs on Erin's home PC, exposed via Cloudflare Tunnel (no cloud costs)

---

## Architecture

```
frontend/          Next.js 14 + TypeScript + Tailwind CSS
                   Full chat UI with sidebar, dark mode, chat history
                   Admin panel for knowledge base management

backend/           Python + FastAPI
                   Ollama API wrapper (qwen2.5-coder:7b)
                   SQLite DB: Knowledge, PendingKnowledge, User tables
                   Discord bot with approval workflow (discord.py)
                   Internal HTTP notify server on port 8001
```

**Live URLs:**
- Chat frontend: `https://chat.erinskidds.com`
- Backend API: `https://api.erinskidds.com`
- Portfolio widget: `https://erinskidds.com`

**Windows Services (NSSM):**
- `SashaBackend` — FastAPI on port 8000
- `SashaFrontend` — Next.js on port 3001
- `SashaDiscordBot` — Discord bot + notify server on port 8001
- `OllamaService` — Ollama on port 11434

---

## Getting Started (Local Development)

### Backend
```powershell
cd backend
pip install -r requirements.txt
# Copy .env.example to .env and fill in values
python main.py
# API runs at http://localhost:8000
```

### Discord Bot
```powershell
cd backend
python discord_bot.py
# Requires DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, DISCORD_CHANNEL_ID, DISCORD_OWNER_ID in .env
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
# UI runs at http://localhost:3000
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI, Uvicorn |
| AI Model | Ollama (qwen2.5-coder:7b) |
| Database | SQLite via SQLAlchemy |
| Discord Bot | discord.py, aiohttp |
| Auth | JWT (python-jose + bcrypt) |
| Tunnel | Cloudflare Tunnel (cloudflared) |
| Services | NSSM (Windows service manager) |
