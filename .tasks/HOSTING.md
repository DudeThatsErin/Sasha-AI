# Hosting Sasha-AI — Exposing Your Local Server to the Internet

**Goal:** Run the backend on your Windows PC at home and make it accessible at `api.erinskidds.com`, and the frontend at `chat.erinskidds.com`.

---

## Overview

| Component | Runs On | Public URL |
|-----------|---------|------------|
| Backend (FastAPI) | Your PC (localhost:8000) | `api.erinskidds.com` |
| Frontend (Next.js) | Vercel (free) OR your PC | `chat.erinskidds.com` |

The recommended approach is **Cloudflare Tunnel** for the backend (already referenced in the backend README) and **Vercel** for the frontend. This avoids opening ports on your router and gives you free HTTPS.

---

## Part 1 — Backend (Your PC → Internet via Cloudflare Tunnel)

### Prerequisites
- A Cloudflare account (free): https://cloudflare.com
- Your domain (`erinskidds.com`) added to Cloudflare with DNS managed there
- `cloudflared` installed on your Windows PC

### Step 1 — Install cloudflared
```powershell
# Option A: Chocolatey
choco install cloudflared

# Option B: Download the .exe directly
# https://github.com/cloudflare/cloudflared/releases/latest
# Download cloudflared-windows-amd64.exe, rename to cloudflared.exe
# Add it to a folder in your PATH (e.g., C:\tools\)
```

### Step 2 — Log in to Cloudflare
```powershell
cloudflared tunnel login
```
A browser window will open. Authorize the domain `erinskidds.com`.

### Step 3 — Create the Tunnel
```powershell
cloudflared tunnel create sasha-ai-backend
```
This creates a tunnel and saves credentials to:
`C:\Users\<YourUsername>\.cloudflared\<tunnel-id>.json`

Note the tunnel ID printed in the output — you'll need it.

### Step 4 — Create the Tunnel Config File
Create the file: `C:\Users\<YourUsername>\.cloudflared\config.yml`

```yaml
tunnel: sasha-ai-backend
credentials-file: C:\Users\<YourUsername>\.cloudflared\<tunnel-id>.json

ingress:
  - hostname: api.erinskidds.com
    service: http://localhost:8000
  - service: http_status:404
```

Replace `<YourUsername>` and `<tunnel-id>` with your actual values.

### Step 5 — Create the DNS Record
```powershell
cloudflared tunnel route dns sasha-ai-backend api.erinskidds.com
```
This adds a CNAME record in Cloudflare DNS automatically.

### Step 6 — Start the Backend + Tunnel

**Terminal 1 — Start the FastAPI backend:**
```powershell
cd F:\repos\Sasha-AI\backend
python main.py
```
Backend will be running at `http://localhost:8000`.

**Terminal 2 — Start the Cloudflare Tunnel:**
```powershell
cloudflared tunnel run sasha-ai-backend
```

Test it: `https://api.erinskidds.com/health` should return `{"status": "healthy", ...}`

### Step 7 — Run the Tunnel as a Windows Service (so it starts automatically)
```powershell
# Run as Administrator
cloudflared service install
```
This registers `cloudflared` as a Windows service that auto-starts on boot.
You still need to start the Python backend separately (see Step 8).

### Step 8 — Auto-Start the Backend on Boot (Optional)
Create a scheduled task or use NSSM (Non-Sucking Service Manager):

```powershell
# Install NSSM
choco install nssm

# Create a service for the backend
nssm install SashaAIBackend "C:\path\to\python.exe" "F:\repos\Sasha-AI\backend\main.py"
nssm set SashaAIBackend AppDirectory "F:\repos\Sasha-AI\backend"
nssm start SashaAIBackend
```

Or simpler: add a shortcut to `python main.py` in your Windows Startup folder
(`shell:startup` in Run dialog).

---

## Part 2 — Frontend (Deploy to Vercel — Recommended)

The Next.js frontend can be deployed for free on Vercel. It will call your backend at `api.erinskidds.com`.

### Step 1 — Update the API URL in the Frontend
Before deploying, make sure `frontend/src/config/api.ts` points to the production backend:

```typescript
// In production, this should be:
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.erinskidds.com'
```

Set the environment variable in Vercel's dashboard (see Step 4).

### Step 2 — Push Frontend to GitHub
```powershell
cd F:\repos\Sasha-AI\frontend
git init  # if not already a git repo
git add .
git commit -m "Initial frontend deploy"
git remote add origin https://github.com/DudeThatsErin/sasha-ai-frontend
git push -u origin main
```

### Step 3 — Deploy on Vercel
1. Go to https://vercel.com and log in with GitHub
2. Click **Add New Project**
3. Import your `sasha-ai-frontend` repository
4. Set **Framework Preset** to `Next.js`
5. Set **Root Directory** to `frontend` (since it's a subdirectory)
6. Click **Deploy**

### Step 4 — Set Environment Variables in Vercel
In your Vercel project → Settings → Environment Variables, add:
```
NEXT_PUBLIC_API_URL = https://api.erinskidds.com
```

### Step 5 — Add Custom Domain
1. In Vercel project → Settings → Domains
2. Add `chat.erinskidds.com`
3. Vercel will give you a CNAME value — add it in Cloudflare DNS:
   - Type: `CNAME`
   - Name: `chat`
   - Target: `cname.vercel-dns.com`
   - Proxy: **OFF** (grey cloud, not orange) — Vercel handles SSL itself

---

## Part 3 — Alternative: Run Frontend Locally Too

If you don't want to use Vercel, you can run the frontend on your PC and expose it via a second Cloudflare Tunnel ingress rule:

```yaml
# config.yml — add a second ingress rule
ingress:
  - hostname: api.erinskidds.com
    service: http://localhost:8000
  - hostname: chat.erinskidds.com
    service: http://localhost:3000
  - service: http_status:404
```

Then run:
```powershell
# Terminal 1
cd F:\repos\Sasha-AI\backend && python main.py

# Terminal 2
cd F:\repos\Sasha-AI\frontend && npm run build && npm start

# Terminal 3
cloudflared tunnel run sasha-ai-backend
```

---

## Part 4 — Keeping It Running

### Daily Startup Checklist
- [ ] Ensure PC is on and not sleeping (disable sleep in Power Settings)
- [ ] Backend running: `http://localhost:8000/health`
- [ ] Tunnel running: check `https://api.erinskidds.com/health`
- [ ] Frontend accessible: `https://chat.erinskidds.com`

### Prevent PC Sleep
Control Panel → Power Options → Change plan settings → Set "Put the computer to sleep" to **Never** (at least while you want the bot available).

### Monitor Uptime (Optional)
Use a free uptime monitor like https://uptimerobot.com to ping `https://api.erinskidds.com/health` every 5 minutes and email you if it goes down.

---

## Part 5 — Security Checklist Before Going Live

- [ ] Change `SECRET_KEY` in `lib/auth.py` to a random string loaded from `.env`
- [ ] Change the default admin password from `admin123`
- [ ] Add rate limiting to the `/chat` endpoint (prevent abuse)
  - Simple option: add `slowapi` to requirements and decorate `/chat` with a rate limit
- [ ] Consider adding a simple honeypot or CAPTCHA if you get spam
- [ ] Keep your PC's Windows Firewall on — Cloudflare Tunnel does NOT require opening any inbound ports

---

## Quick Reference — Commands to Start Everything

```powershell
# 1. Start backend (Terminal 1)
cd F:\repos\Sasha-AI\backend
python main.py

# 2. Start Cloudflare tunnel (Terminal 2)
cloudflared tunnel run sasha-ai-backend

# 3. (If running frontend locally) Start frontend (Terminal 3)
cd F:\repos\Sasha-AI\frontend
npm run dev
```
