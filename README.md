# Personal AI OS

**One AI interface for your entire digital life.**

Production-oriented, multi-user SaaS foundation with complete data isolation per user.

## Features Implemented

| Area | Status |
|------|--------|
| Multi-user registration / login / JWT | ✅ |
| User data isolation (all queries scoped by JWT user) | ✅ |
| AI Chat + conversation history | ✅ |
| Long-term memory (CRUD + search) | ✅ |
| Task manager | ✅ |
| Connected Apps dashboard (Gmail, Calendar, Drive, Slack, Notion, WhatsApp) | ✅ |
| Google OAuth flow skeleton (requires real credentials) | ✅ |
| AI provider abstraction (OpenAI-compatible) | ✅ |
| Tool registry + agent foundation | ✅ |
| Daily planner | ✅ |
| Activity / audit log API | ✅ |
| Dashboard UI (Next.js + Tailwind) | ✅ |
| PostgreSQL + async SQLAlchemy + Alembic | ✅ |
| pgvector-ready models (embeddings as JSONB for now) | ✅ |

## Quick Start (Windows)

### 1. PostgreSQL

```powershell
# With Docker (recommended)
cd personal-ai-os
docker compose up -d
```

### 2. Backend

```powershell
cd personal-ai-os\backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env: set SECRET_KEY, OPENAI_API_KEY, and optionally Google OAuth credentials
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify:
- http://localhost:8000/docs
- http://localhost:8000/health/db → `"database": "connected"`

### 3. Frontend

```powershell
cd personal-ai-os\frontend
npm install
npm run dev
```

Open http://localhost:3000

### 4. First use

1. Register a new account
2. Login
3. Explore Dashboard, Chat, Memory, Tasks, Connected Apps
4. Set `OPENAI_API_KEY` in backend `.env` for real AI replies

## Environment Variables

See `backend/.env.example` for the full list.

Critical:
- `SECRET_KEY` — change for production
- `DATABASE_URL` / `DATABASE_URL_SYNC`
- `OPENAI_API_KEY` — for AI chat & embeddings
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — for Gmail/Calendar/Drive OAuth

## Architecture

```
User → JWT Auth → Personal AI OS Dashboard
         ↓
    AI Chat / Voice
         ↓
    AI Agent
         ↓
    Tool Registry → Permission Check → Tool → External API / DB
         ↓
    Activity Log
```

**Security rules enforced:**
- Never trust `user_id` from the frontend — always derived from JWT
- OAuth tokens stored only on the backend, never returned to the client
- All DB queries filter by `current_user.id`
- Sensitive actions designed to require confirmation

## Project Structure

```
personal-ai-os/
├── backend/
│   ├── app/
│   │   ├── api/          # auth, chat, memory, tasks, integrations, activity, planner
│   │   ├── agents/       # tool_registry
│   │   ├── core/         # config, security
│   │   ├── database/     # session, base
│   │   ├── models/       # user, conversation, memory, task, connected_account, ...
│   │   ├── schemas/
│   │   ├── services/     # ai_service, activity_service
│   │   └── main.py
│   ├── alembic/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/              # Next.js App Router pages
│   ├── components/
│   └── lib/api.ts
├── docker-compose.yml    # PostgreSQL + pgvector
└── README.md
```

## External Integrations

OAuth connection endpoints and UI are in place. To enable real Google integrations:

1. Create a project in Google Cloud Console
2. Enable Gmail, Calendar, Drive APIs
3. Create OAuth 2.0 credentials
4. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and the redirect URI
5. Complete the token exchange logic in the callback (placeholder currently logs receipt of the code)

Same pattern for Notion and Slack.

WhatsApp uses the official WhatsApp Business API approach and is marked as requiring configuration.

## Development Notes

- In development, tables are auto-created on startup (`init_db`).
- Prefer Alembic migrations for production schema changes.
- AI works without a key (returns a configuration message); set the key for real completions.
- Multi-user isolation is enforced at every query level.

## Next Hardening Opportunities

- Encrypt OAuth tokens at rest
- Rate limiting middleware
- Full agent multi-step tool execution loop
- Streaming chat responses
- Document upload + RAG pipeline
- Voice STT/TTS abstraction
- Production deployment (Vercel + Render/Railway + Neon)

## License

Private / adjust as needed.
