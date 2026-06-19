# MemoraAI

Production-grade AI retrieval system with hybrid search, memory, and explainable responses.

## 🎯 Features

- **Hybrid Retrieval**: Vector search (pgvector) + BM25 (PostgreSQL FTS) + RRF fusion
- **Cross-Encoder Reranking**: Semantic relevance scoring with ms-marco-MiniLM-L-6-v2
- **Layered Memory**: Short-term, long-term, and episodic memory
- **Adaptive Query Routing**: Smart retrieval strategy selection
- **Explainable AI**: Source attribution and confidence scores
- **Production Ready**: Docker, monitoring, error handling

## 🚀 Quick Start with Supabase

### 1. Set Up Supabase Database

1. Create account at https://supabase.com
2. Create new project named "MemoraAI"
3. Go to **SQL Editor** and run `db/schema.sql`
4. Get connection string from **Settings > Database**

### 2. Configure Environment

```bash
cd MemoraAI
copy .env.example .env
```

Edit `.env`:
```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Start AI Service

```bash
cd ai-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Start Backend (New Terminal)

```bash
cd backend
npm install
npm run start:dev
```

### 5. Start Frontend (New Terminal)

```bash
cd frontend
npm install
npm run dev
```

---

## 🌐 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3001 | Next.js UI |
| Backend | http://localhost:3000 | NestJS API |
| AI Service | http://localhost:8000 | FastAPI |
| API Docs | http://localhost:8000/docs | Swagger UI |

---

## 📁 Project Structure

```
memora-ai/
├── ai-service/          # Python FastAPI - Hybrid retrieval, memory, generation
├── backend/             # NestJS - API orchestration, middleware, validation
├── frontend/            # Next.js 15 - Chat UI, retrieval panel, memory display
├── db/
│   └── schema.sql      # PostgreSQL + pgvector schema
├── docs/
│   ├── LOCAL_SETUP.md   # Detailed setup guide
│   ├── PRD.md          # Product requirements
│   └── ARCHITECTURE_NOTES.md
└── docker-compose.yml   # Full stack orchestration
```

---

## 🔧 Detailed Setup Guide

For complete step-by-step instructions, see [docs/LOCAL_SETUP.md](./docs/LOCAL_SETUP.md)

---

## 🐳 Docker Compose (All-in-One)

```bash
# Configure .env with Supabase connection string and API keys
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 🧪 Testing the Setup

### Test AI Service Health
```bash
curl http://localhost:8000/api/v1/health
```

### Test Ingestion
```bash
curl -X POST http://localhost:8000/api/v1/ingest/text `
  -H "Content-Type: application/json" `
  -d "{\"text\": \"Test content\", \"source\": \"test\"}"
```

### Test Query
```bash
curl -X POST http://localhost:8000/api/v1/query `
  -H "Content-Type: application/json" `
  -d "{\"query\": \"Hello\", \"session_id\": \"test\"}"
```

---


## ⚙️ Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, Framer Motion |
| Backend | NestJS, TypeScript, Zod, class-validator |
| AI Service | Python, FastAPI, asyncpg, pgvector, sentence-transformers |
| Database | PostgreSQL + pgvector |
| AI | Gemini 2.5 Flash, text-embedding-004 |


## 🔧 Troubleshooting

### Database Connection Issues
1. Check Supabase project is not paused
2. Verify connection string format
3. Allow your IP in Settings > Database > Network

### Port Already in Use
```bash
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

### Python Import Errors
```bash
cd ai-service
pip install -r requirements.txt --force-reinstall
```