# Hosting Sasha-AI — Exposing Your Local Server to the Internet

**Goal:** Run the backend on your Windows PC at home and make it accessible at `api.erinskidds.com`, and the frontend at `chat.erinskidds.com`.

---

## Overview

| Component | Runs On | Public URL |
|-----------|---------|------------|
| Backend (FastAPI) | Your PC (localhost:8000) | `api.erinskidds.com` |
| Frontend (Next.js) | Oracle Cloud Server | `chat.erinskidds.com` |

The recommended approach is:
- **Backend** — Cloudflare Tunnel from your Windows PC (no port forwarding needed, free HTTPS)
- **Frontend** — Oracle Cloud server (always-on, not dependent on your PC being awake)

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

## Part 2 — Frontend (Oracle Cloud Server)

The Next.js frontend runs on your Oracle Cloud server as a Node.js process managed by PM2. It will call your backend at `api.erinskidds.com`.

### Prerequisites on the Oracle Server
- Ubuntu (or Oracle Linux) with Node.js 18+ installed
- PM2 installed globally: `npm install -g pm2`
- Nginx installed: `sudo apt install nginx`
- Your domain's `chat` subdomain pointed at the Oracle server's public IP (see Step 6)

### Step 1 — Update the API URL in the Frontend
Before deploying, make sure `frontend/src/config/api.ts` points to the production backend:

```typescript
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.erinskidds.com'
```

Create a `.env.production` file in `frontend/`:
```
NEXT_PUBLIC_API_URL=https://api.erinskidds.com
```

### Step 2 — Copy the Frontend to the Oracle Server

**Option A — Git (recommended):**
```bash
# On the Oracle server
git clone https://github.com/DudeThatsErin/sasha-ai frontend
cd frontend/frontend
npm install
npm run build
```

**Option B — SCP/SFTP from your PC:**
```powershell
# From your Windows PC — copy the built output
scp -r F:\repos\Sasha-AI\frontend user@<oracle-ip>:/home/user/sasha-frontend
```
Then on the server: `npm install && npm run build`

### Step 3 — Run the Frontend with PM2
```bash
# On the Oracle server, from the frontend/ directory
pm2 start npm --name "sasha-frontend" -- start
pm2 save
pm2 startup   # follow the printed command to enable auto-start on reboot
```

The Next.js app will run on port `3000` by default.

### Step 4 — Configure Nginx as a Reverse Proxy

Create `/etc/nginx/sites-available/sasha-frontend`:
```nginx
server {
    listen 80;
    server_name chat.erinskidds.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable it:
```bash
sudo ln -s /etc/nginx/sites-available/sasha-frontend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 5 — Enable HTTPS with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d chat.erinskidds.com
# Certbot will auto-update the Nginx config and set up auto-renewal
```

### Step 6 — Point DNS to the Oracle Server
In Cloudflare DNS, add:
- Type: `A`
- Name: `chat`
- Value: `<your Oracle server public IP>`
- Proxy: **ON** (orange cloud) — routes through Cloudflare CDN for DDoS protection

### Step 7 — Open the Port on Oracle Cloud
Oracle Cloud blocks inbound traffic by default. You need to open ports 80 and 443:
1. In Oracle Cloud Console → Networking → Virtual Cloud Networks → your VCN
2. Click your subnet → Security List → Add Ingress Rules:
   - Source: `0.0.0.0/0`, Protocol: TCP, Port: `80`
   - Source: `0.0.0.0/0`, Protocol: TCP, Port: `443`
3. Also run on the server:
```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save   # install with: sudo apt install iptables-persistent
```

### Updating the Frontend After Code Changes
```bash
# On the Oracle server
cd /home/user/sasha-frontend/frontend
git pull
npm install
npm run build
pm2 restart sasha-frontend
```

---

## Part 3 — Alternative: Deploy Frontend to Vercel Instead

If you'd rather not manage the Oracle server for the frontend, Vercel is a free alternative:

1. Push the repo to GitHub
2. Go to https://vercel.com → Add New Project → import the repo
3. Set **Root Directory** to `frontend`
4. Add environment variable: `NEXT_PUBLIC_API_URL = https://api.erinskidds.com`
5. Add custom domain `chat.erinskidds.com` in Vercel settings
6. In Cloudflare DNS: `CNAME chat → cname.vercel-dns.com` with proxy **OFF**

> **Note:** Vercel's free tier has a 10-second serverless function timeout. Since this is a static/client-rendered chat app that calls your own backend, this is not an issue.

---

## Part 4 — Keeping It Running

### Startup Checklist
- [ ] **PC** — on and not sleeping (backend + tunnel run here)
- [ ] Backend running: `http://localhost:8000/health`
- [ ] Cloudflare Tunnel running: check `https://api.erinskidds.com/health`
- [ ] Oracle server — PM2 process running: `pm2 list` (should show `sasha-frontend` as `online`)
- [ ] Frontend accessible: `https://chat.erinskidds.com`

### Prevent PC Sleep (Backend Only)
Control Panel → Power Options → Change plan settings → Set "Put the computer to sleep" to **Never**.

> The frontend on Oracle runs 24/7 regardless of your PC state. Only the backend (and therefore the AI responses) goes down if your PC sleeps or reboots.

### Monitor Uptime (Optional)
Use a free uptime monitor like https://uptimerobot.com:
- Ping `https://api.erinskidds.com/health` every 5 min → alerts you if your PC/tunnel goes down
- Ping `https://chat.erinskidds.com` every 5 min → alerts you if the Oracle server/PM2 goes down

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

**On your Windows PC (backend):**
```powershell
# Terminal 1 — FastAPI backend
cd F:\repos\Sasha-AI\backend
python main.py

# Terminal 2 — Cloudflare Tunnel
cloudflared tunnel run sasha-ai-backend
```

**On the Oracle server (frontend — managed by PM2, auto-starts on reboot):**
```bash
# Check status
pm2 list

# Restart if needed
pm2 restart sasha-frontend

# View logs
pm2 logs sasha-frontend
```

**Deploy a frontend update:**
```bash
cd /home/user/sasha-frontend/frontend
git pull && npm install && npm run build && pm2 restart sasha-frontend
```
