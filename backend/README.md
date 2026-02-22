# Sasha AI Backend

FastAPI backend for Sasha AI — a portfolio chatbot powered by a local Ollama model. Knowledge is stored in SQLite and managed via a web admin panel and Discord bot.

## 📁 Project Structure

```
backend/
├── config/
│   ├── app_config.py                # API, Ollama, CORS, and Discord settings
│   ├── system_prompt.txt            # Seed data — imported to DB on first run
│   └── collected_conversations.json # Chat logs saved at runtime (auto-created)
├── lib/
│   ├── auth.py                      # JWT authentication helpers
│   ├── conversation_collector.py    # Saves every chat turn for review
│   ├── database.py                  # SQLite/SQLAlchemy: Knowledge, PendingKnowledge, User
│   ├── knowledge_manager.py         # Builds system prompt dynamically from DB
│   └── model_manager.py             # Ollama API wrapper
├── logs/                            # Application and Discord bot logs
├── routes/
│   └── auth.py                      # Auth endpoints (login, register)
├── discord_bot.py                   # Discord bot: approval buttons + slash commands
├── main.py                          # FastAPI app entry point
├── .env.example                     # Environment variable template
└── requirements.txt                 # Python dependencies
```

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Ensure Ollama is running
```bash
ollama serve
ollama pull qwen2.5-coder:7b
```

### 3. Start the backend
```bash
python main.py
```

### 4. Verify it's working
```bash
curl http://localhost:8000/health
```

## 🧠 How Sasha Learns About Erin

Knowledge is stored in a SQLite database (`Knowledge` table) and built into the system prompt dynamically on each request. `system_prompt.txt` is only used to seed the DB on first startup.

**To manage knowledge:**
- **Admin UI**: `https://chat.erinskidds.com/admin` — full CRUD, enable/disable entries, pending approval queue
- **Discord slash commands**: `/knowledge-add`, `/knowledge-list`, `/knowledge-delete`, `/knowledge-toggle`

**Approval workflow (teach-intent):**
1. Visitor says something like "remember that Erin also speaks Spanish"
2. Backend detects the teach intent → creates a `PendingKnowledge` entry → Sasha responds "let me ask Erin"
3. Discord bot pings Erin with ✅ Yes / ❌ No buttons
4. On approval → entry moves to live `Knowledge` table and Sasha knows it immediately

## 🎯 API Endpoints

### Chat
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/chat` | None | Send a message; detects teach-intent automatically |
| `GET` | `/health` | None | Health check |
| `GET` | `/` | None | Server status + conversation count |

### Knowledge Base
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/knowledge` | None | List all knowledge entries |
| `POST` | `/knowledge` | None | Add a new entry |
| `PUT` | `/knowledge/{id}` | None | Update an entry |
| `DELETE` | `/knowledge/{id}` | None | Delete an entry |

### Pending Knowledge (Approval Queue)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/pending-knowledge` | None | List all pending entries |
| `POST` | `/pending-knowledge/{id}/approve` | None | Approve → moves to Knowledge table |
| `POST` | `/pending-knowledge/{id}/deny` | None | Deny → marks as denied |

### Conversation Logs
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/conversations/stats` | None | Total chats and unique sessions |
| `DELETE` | `/conversations` | None | Clear all saved conversations |

### Model
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/model/status` | None | Ollama availability and model info |
| `POST` | `/model/reload` | None | Re-check Ollama without restarting |

### Auth (admin only)
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/login` | Get JWT token |
| `POST` | `/auth/register` | Create user |

## 📊 API Examples

### Send a message
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your tech stack?", "chat_id": "test-1"}'
```

### Send with conversation history
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me more about that.",
    "chat_id": "test-1",
    "history": [
      {"role": "user", "content": "What is your tech stack?"},
      {"role": "assistant", "content": "I work mainly with TypeScript, React, and Python..."}
    ]
  }'
```

### Check stats
```bash
curl "http://localhost:8000/conversations/stats"
```

Response:
```json
{
  "total_conversations": 12,
  "unique_chats": 4
}
```

## ⚙️ Configuration

All settings live in `config/app_config.py` and `.env`:

| Setting | Default | Description |
|---------|---------|-------------|
| `OLLAMA_URL` | `http://localhost:11434` | Override with env var |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Override with env var |
| `MAX_NEW_TOKENS` | `500` | Max response length |
| `TEMPERATURE` | `0.8` | Response creativity |
| `CORS_ORIGINS` | `localhost`, `*.erinskidds.com` | Allowed frontend origins |
| `DISCORD_BOT_TOKEN` | — | Required for Discord bot |
| `DISCORD_GUILD_ID` | — | Your Discord server ID |
| `DISCORD_CHANNEL_ID` | — | Channel for approval pings |
| `DISCORD_OWNER_ID` | — | Your Discord user ID |
| `DISCORD_NOTIFY_PORT` | `8001` | Internal notify server port |

Copy `.env.example` to `.env` and fill in all values before starting.

## � Security

Before going public, move `SECRET_KEY` out of `lib/auth.py` and into an environment variable:

```bash
# backend/.env
SECRET_KEY=your-random-32-char-string-here
SASHA_ENV=production
```

Then load it in `lib/auth.py`:
```python
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-only-for-dev")
```

Ensure `.env` is in `.gitignore`.

## 🔧 Troubleshooting

**Sasha isn't responding / 500 errors**
- Check Ollama is running: `ollama serve`
- Check the model is pulled: `ollama list`
- Hit `/health` — look for `"ollama": {"running": true}`

**Sasha doesn't know something about Erin**
- Add it via the admin UI at `chat.erinskidds.com/admin` or use `/knowledge-add` in Discord
- `system_prompt.txt` is only used to seed the DB on first run — editing it won't affect a running instance

**Import errors on startup**
- Run `pip install -r requirements.txt` from the `backend/` directory

## 🌐 Hosting with Cloudflare Tunnel

To expose the local backend publicly (for the portfolio widget at `api.erinskidds.com`):

### Setup

```bash
# Install cloudflared (Windows)
choco install cloudflared
# or download from https://github.com/cloudflare/cloudflared/releases

cloudflared tunnel login
cloudflared tunnel create sasha-ai-backend
cloudflared tunnel route dns sasha-ai-backend api.erinskidds.com
```

Create `~/.cloudflared/config.yml`:
```yaml
tunnel: sasha-ai-backend
credentials-file: C:\Users\[username]\.cloudflared\[tunnel-id].json

ingress:
  - hostname: api.erinskidds.com
    service: http://localhost:8000
  - service: http_status:404
```

### Run

```bash
# Terminal 1
python main.py

# Terminal 2
cloudflared tunnel run sasha-ai-backend
```

The portfolio widget will reach the backend at `https://api.erinskidds.com/chat`.

## 🤖 Discord Bot

The Discord bot runs as a separate NSSM service (`SashaDiscordBot`) and handles:
- Pinging Erin when a new teach-intent is detected
- ✅ Yes / ❌ No approval buttons on pending knowledge entries
- Slash commands: `/knowledge-list`, `/knowledge-add`, `/knowledge-delete`, `/knowledge-toggle`, `/pending-list`, `/pending-approve`, `/pending-deny`

```powershell
# Run manually (for testing)
python discord_bot.py

# Or manage via NSSM
nssm start SashaDiscordBot
nssm restart SashaDiscordBot
```

Logs: `logs/discord_bot.log` and `logs/discord_bot_err.log`
