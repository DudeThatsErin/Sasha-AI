# Sasha AI Frontend

Next.js 14 chat interface for Sasha AI — Erin's personal portfolio chatbot. Includes a full chat UI, knowledge base admin panel, and dark/light mode.

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── admin/
│   │   │   └── page.tsx         # Knowledge base admin panel
│   │   ├── globals.css          # Global styles + Tailwind
│   │   ├── layout.tsx           # Root layout
│   │   └── page.tsx             # Main chat page
│   ├── components/
│   │   ├── ChatInterface.tsx    # Main chat UI (messages, input, header)
│   │   ├── ChatMessage.tsx      # Individual message renderer (markdown links)
│   │   ├── Sidebar.tsx          # Chat history sidebar
│   │   ├── ThemeProvider.tsx    # Dark/light mode context
│   │   └── Toast.tsx            # Toast notifications
│   ├── config/
│   │   └── api.ts               # API base URL + endpoints
│   ├── lib/
│   │   ├── database.ts          # localStorage chat persistence
│   │   └── titleGenerator.ts   # Auto-generates chat titles
│   └── types/
│       └── chat.ts              # Chat and Message TypeScript types
├── public/                      # Static assets
├── next.config.js
├── tailwind.config.js
└── package.json
```

## 🚀 Quick Start

```powershell
npm install
npm run dev
# UI runs at http://localhost:3000
```

For production build:
```powershell
npm run build
npm start
```

## 🧠 Features

- **Chat history** — persisted in `localStorage`, survives page refreshes
- **Sidebar** — browse and switch between past conversations
- **Dark/light mode** — toggle in the header, saved to `localStorage`
- **Widget import** — when opened from the portfolio widget via `?import_chat=<id>`, automatically imports the widget conversation
- **Offline message** — when the backend is unreachable, shows a friendly message with clickable LinkedIn and GitHub links
- **Teach-intent UI** — when Sasha detects a teach request, shows the "let me ask Erin" response
- **Admin panel** — two tabs: Knowledge Base (full CRUD) and Pending Approval (approve/deny queue with badge count)
- **Markdown links** — message content renders `[text](url)` as clickable anchor tags

## ⚙️ Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=https://api.erinskidds.com
NEXT_PUBLIC_SASHA_FRONTEND_URL=https://chat.erinskidds.com
```

For local development these default to `http://localhost:8000` and `http://localhost:3000` automatically.