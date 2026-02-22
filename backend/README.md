# Sasha AI Backend

FastAPI backend for Sasha AI — a portfolio chatbot powered by a local Ollama model. No training required; Sasha's personality and knowledge come entirely from a system prompt.

## 📁 Project Structure

```
backend/
├── config/
│   ├── app_config.py                # API, Ollama, and CORS settings
│   ├── system_prompt.txt            # ← Edit this to update what Sasha knows about Erin
│   └── collected_conversations.json # Chat logs saved at runtime (auto-created)
├── lib/
│   ├── auth.py                      # JWT authentication helpers
│   ├── conversation_collector.py    # Saves every chat turn for review
│   ├── database.py                  # SQLite/SQLAlchemy setup
│   └── model_manager.py             # Ollama API wrapper
├── logs/                            # Application logs
├── routes/
│   └── auth.py                      # Auth endpoints (login, register)
├── main.py                          # FastAPI app entry point
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

There is no training step. Edit `config/system_prompt.txt` directly — the backend reads it on startup. Restart the server after any changes.

The prompt already contains Erin's full work history, tech stack, projects, personality, and contact info. Add or update anything there.

## 🎯 API Endpoints

### Chat
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/chat` | None | Send a message, get a response |
| `GET` | `/health` | None | Health check |
| `GET` | `/` | None | Server status + conversation count |

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

All settings live in `config/app_config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `OLLAMA_URL` | `http://localhost:11434` | Override with `OLLAMA_URL` env var |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Override with `OLLAMA_MODEL` env var |
| `MAX_NEW_TOKENS` | `500` | Max response length |
| `TEMPERATURE` | `0.8` | Response creativity |
| `CORS_ORIGINS` | `localhost`, `*.erinskidds.com` | Allowed frontend origins |

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
- Edit `config/system_prompt.txt` and restart the backend

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
