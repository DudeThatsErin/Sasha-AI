# Embedding Sasha — Floating Chat Widget in the Portfolio

**Primary method:** Floating chat bubble widget built directly into the portfolio repo.
**Fallback / standalone:** `chat.erinskidds.com` (the full Sasha-AI frontend, linked from the portfolio).

---

## Overview

The widget is a small floating button (bottom-right corner) that opens a chat panel inline on the page. Visitors never leave the portfolio — they just click the bubble and start chatting with Sasha.

```
Portfolio page
└── Floating bubble button (bottom-right, always visible)
    └── Opens chat panel (iframe OR inline component)
        └── Calls api.erinskidds.com/chat
```

---

## Which Portfolio?

You have two portfolio repos:

| Repo | Stack | Widget Approach |
|------|-------|-----------------|
| `portfolio-next/` | Next.js 16 + Tailwind | **React component** (best option) |
| `Portfolio/` | PHP + vanilla JS/CSS | **Vanilla JS + CSS snippet** injected via `footer.php` |

Pick the one that's live. Instructions for both are below.

---

## Option A — Next.js Portfolio (`portfolio-next/`)

### Step 1 — Create the Widget Component

Create `f:\repos\portfolio-next\src\components\SashaWidget.tsx`:

```tsx
'use client'

import { useState, useRef, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_SASHA_API_URL || 'https://api.erinskidds.com'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function SashaWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: "Hi! I'm Sasha, Erin's AI. Ask me anything about her — her work, projects, tech stack, or just say hi!" }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const chatId = useRef(`widget-${Date.now()}`)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage() {
    const text = input.trim()
    if (!text || loading) return

    const userMsg: Message = { role: 'user', content: text }
    const updatedMessages = [...messages, userMsg]
    setMessages(updatedMessages)
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          chat_id: chatId.current,
          history: updatedMessages.slice(1, -1), // exclude greeting and current message
        }),
      })
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I'm offline right now. Try reaching Erin directly!" }])
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <>
      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-24 right-4 z-50 w-80 sm:w-96 h-[480px] bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-indigo-600 text-white">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-indigo-400 flex items-center justify-center font-bold text-sm">S</div>
              <div>
                <p className="font-semibold text-sm leading-none">Sasha</p>
                <p className="text-xs text-indigo-200">Erin's AI</p>
              </div>
            </div>
            <button
              onClick={() => setOpen(false)}
              aria-label="Close chat"
              className="text-indigo-200 hover:text-white text-xl leading-none"
            >
              ×
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white rounded-br-sm'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-bl-sm'
                }`}>
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-bl-sm px-3 py-2 text-sm text-gray-500">
                  Thinking…
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="px-3 py-3 border-t border-gray-200 dark:border-gray-700 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask me anything…"
              disabled={loading}
              className="flex-1 text-sm rounded-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-2 outline-none focus:border-indigo-500"
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              aria-label="Send"
              className="w-9 h-9 rounded-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white flex items-center justify-center shrink-0"
            >
              ↑
            </button>
          </div>

          {/* Footer link */}
          <p className="text-center text-xs text-gray-400 pb-2">
            <a href="https://chat.erinskidds.com" target="_blank" rel="noopener noreferrer" className="hover:underline">
              Open full chat →
            </a>
          </p>
        </div>
      )}

      {/* Floating bubble button */}
      <button
        onClick={() => setOpen(o => !o)}
        aria-label={open ? 'Close Sasha chat' : 'Chat with Sasha, Erin\'s AI'}
        className="fixed bottom-4 right-4 z-50 w-14 h-14 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg flex items-center justify-center text-2xl transition-transform hover:scale-105"
      >
        {open ? '×' : '💬'}
      </button>
    </>
  )
}
```

### Step 2 — Add to the Root Layout

Open `f:\repos\portfolio-next\src\app\layout.tsx` and add the widget inside the `<body>`:

```tsx
import SashaWidget from '@/components/SashaWidget'

// Inside the return, after your existing content:
<body>
  {/* ... existing layout ... */}
  <SashaWidget />
</body>
```

### Step 3 — Add the Environment Variable

In `f:\repos\portfolio-next\.env.local` (create if it doesn't exist):
```
NEXT_PUBLIC_SASHA_API_URL=https://api.erinskidds.com
```

For local development testing (backend running locally):
```
NEXT_PUBLIC_SASHA_API_URL=http://localhost:8000
```

### Step 4 — Test Locally

```powershell
cd F:\repos\portfolio-next
npm run dev
```

Open `http://localhost:3000` — you should see the chat bubble in the bottom-right corner.

---

## Option B — PHP Portfolio (`Portfolio/`)

If the PHP portfolio is the live one, add the widget as a self-contained vanilla JS/CSS snippet.

### Step 1 — Add the Widget Script

At the bottom of `f:\repos\Portfolio\footer.php`, just before the closing `</body>` tag, add:

```html
<!-- Sasha AI Widget -->
<div id="sasha-widget">
  <div id="sasha-panel" style="display:none;">
    <div id="sasha-header">
      <div id="sasha-avatar">S</div>
      <div>
        <strong>Sasha</strong>
        <small>Erin's AI</small>
      </div>
      <button id="sasha-close" aria-label="Close chat">×</button>
    </div>
    <div id="sasha-messages">
      <div class="sasha-msg bot">Hi! I'm Sasha, Erin's AI. Ask me anything about her!</div>
    </div>
    <div id="sasha-input-row">
      <input id="sasha-input" type="text" placeholder="Ask me anything…" />
      <button id="sasha-send" aria-label="Send">↑</button>
    </div>
    <p id="sasha-footer"><a href="https://chat.erinskidds.com" target="_blank" rel="noopener noreferrer">Open full chat →</a></p>
  </div>
  <button id="sasha-bubble" aria-label="Chat with Sasha, Erin's AI">💬</button>
</div>

<style>
#sasha-widget { position: fixed; bottom: 1rem; right: 1rem; z-index: 9999; font-family: sans-serif; }
#sasha-bubble { width: 56px; height: 56px; border-radius: 50%; background: #4f46e5; color: #fff; border: none; font-size: 1.5rem; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: transform .15s; }
#sasha-bubble:hover { transform: scale(1.05); }
#sasha-panel { position: absolute; bottom: 70px; right: 0; width: 320px; height: 460px; background: #fff; border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.18); border: 1px solid #e5e7eb; display: flex; flex-direction: column; overflow: hidden; }
#sasha-header { display: flex; align-items: center; gap: 10px; padding: 12px 16px; background: #4f46e5; color: #fff; }
#sasha-avatar { width: 32px; height: 32px; border-radius: 50%; background: #818cf8; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: .85rem; }
#sasha-header strong { display: block; font-size: .9rem; }
#sasha-header small { font-size: .75rem; color: #c7d2fe; }
#sasha-close { margin-left: auto; background: none; border: none; color: #c7d2fe; font-size: 1.4rem; cursor: pointer; line-height: 1; }
#sasha-close:hover { color: #fff; }
#sasha-messages { flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.sasha-msg { max-width: 80%; padding: 8px 12px; border-radius: 16px; font-size: .85rem; line-height: 1.4; }
.sasha-msg.bot { background: #f3f4f6; color: #111; border-bottom-left-radius: 4px; align-self: flex-start; }
.sasha-msg.user { background: #4f46e5; color: #fff; border-bottom-right-radius: 4px; align-self: flex-end; }
.sasha-msg.thinking { color: #9ca3af; font-style: italic; }
#sasha-input-row { display: flex; gap: 8px; padding: 10px 12px; border-top: 1px solid #e5e7eb; }
#sasha-input { flex: 1; border: 1px solid #d1d5db; border-radius: 999px; padding: 8px 14px; font-size: .85rem; outline: none; }
#sasha-input:focus { border-color: #4f46e5; }
#sasha-send { width: 36px; height: 36px; border-radius: 50%; background: #4f46e5; color: #fff; border: none; cursor: pointer; font-size: 1rem; }
#sasha-send:disabled { opacity: .4; }
#sasha-footer { text-align: center; font-size: .75rem; color: #9ca3af; padding: 0 0 8px; margin: 0; }
#sasha-footer a { color: #9ca3af; text-decoration: none; }
#sasha-footer a:hover { text-decoration: underline; }
</style>

<script>
(function() {
  const API = 'https://api.erinskidds.com';
  const chatId = 'widget-' + Date.now();
  const history = [];
  let loading = false;

  const bubble = document.getElementById('sasha-bubble');
  const panel  = document.getElementById('sasha-panel');
  const closeBtn = document.getElementById('sasha-close');
  const input  = document.getElementById('sasha-input');
  const sendBtn = document.getElementById('sasha-send');
  const msgs   = document.getElementById('sasha-messages');

  bubble.addEventListener('click', () => {
    const isOpen = panel.style.display !== 'none';
    panel.style.display = isOpen ? 'none' : 'flex';
    bubble.textContent = isOpen ? '💬' : '×';
    if (!isOpen) input.focus();
  });

  closeBtn.addEventListener('click', () => {
    panel.style.display = 'none';
    bubble.textContent = '💬';
  });

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  });
  sendBtn.addEventListener('click', send);

  function addMsg(text, type) {
    const div = document.createElement('div');
    div.className = 'sasha-msg ' + type;
    div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    return div;
  }

  async function send() {
    const text = input.value.trim();
    if (!text || loading) return;
    loading = true;
    sendBtn.disabled = true;
    input.value = '';

    addMsg(text, 'user');
    history.push({ role: 'user', content: text });

    const thinking = addMsg('Thinking…', 'bot thinking');

    try {
      const res = await fetch(API + '/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, chat_id: chatId, history: history.slice(0, -1) })
      });
      const data = await res.json();
      thinking.remove();
      addMsg(data.response, 'bot');
      history.push({ role: 'assistant', content: data.response });
    } catch(e) {
      thinking.remove();
      addMsg("Sorry, I'm offline right now. Try reaching Erin directly!", 'bot');
    } finally {
      loading = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }
})();
</script>
```

---

## Fallback — Standalone Chat at `chat.erinskidds.com`

For visitors who want a full-screen experience, or as a fallback if the widget API is down, link to the standalone Sasha-AI frontend.

Add a link anywhere on the portfolio (e.g., in the header or about section):

**Next.js portfolio:**
```tsx
<a href="https://chat.erinskidds.com" target="_blank" rel="noopener noreferrer">
  Chat with Sasha, my AI →
</a>
```

**PHP portfolio:**
```html
<a href="https://chat.erinskidds.com" target="_blank" rel="noopener noreferrer">
  Chat with Sasha, my AI →
</a>
```

The widget already includes an "Open full chat →" link at the bottom of the panel that points there automatically.

---

## Checklist

### Before the widget goes live
- [ ] Backend is running and reachable at `https://api.erinskidds.com/health`
- [ ] `SYSTEM_PROMPT` in `backend/config/app_config.py` is filled in with real Erin info
- [ ] Test the widget locally with `NEXT_PUBLIC_SASHA_API_URL=http://localhost:8000`
- [ ] Confirm multi-turn conversation works (ask a follow-up question)
- [ ] Confirm the "Open full chat →" link goes to `chat.erinskidds.com`
- [ ] Check mobile layout — widget should not cover important content

### Deploying the widget
- [ ] **Next.js portfolio:** add `NEXT_PUBLIC_SASHA_API_URL=https://api.erinskidds.com` to Vercel environment variables (or Oracle server `.env`)
- [ ] **PHP portfolio:** push `footer.php` changes to the server — no build step needed
- [ ] Verify the bubble appears on the live site
- [ ] Send a test message on the live site and confirm a real response comes back

### Nice-to-haves (later)
- [ ] Replace the `S` avatar with Erin's actual photo
- [ ] Add 2–3 suggested starter questions below the greeting message (e.g., "What's your tech stack?", "Tell me about your projects", "How do I contact you?")
- [ ] Add a subtle pulse animation to the bubble on first page load to draw attention
- [ ] Graceful offline state — if `api.erinskidds.com` is unreachable, show a message with a mailto link instead
