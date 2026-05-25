# MemoraAI AI Service

Production-grade AI microservice for adaptive RAG with hybrid retrieval.

## Features

- **Hybrid Retrieval**: Vector search (pgvector) + BM25 (PostgreSQL FTS)
- **Reciprocal Rank Fusion**: Combined ranking from multiple retrieval methods
- **Cross-Encoder Reranking**: Semantic relevance scoring
- **Layered Memory**: Short-term, long-term, and episodic memory
- **Adaptive Query Routing**: Classifies queries for optimal retrieval strategy
- **Prompt Injection Defense**: Content sanitization and validation
- **Observability**: Structured logging and metrics

## Quick Start

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the service
uvicorn app.main:app --reload --port 8000
```

### Docker

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d
```

## Configuration

Environment variables (see `.env.example`):

- `GEMINI_API_KEY`: Google Gemini API key
- `DATABASE_URL`: PostgreSQL connection string
- `CHUNK_SIZE`: Token-based chunk size (default: 700)
- `CHUNK_OVERLAP`: Chunk overlap (default: 100)

## API Endpoints

### Health
- `GET /api/v1/health` - Health check

### Ingestion
- `POST /api/v1/ingest/pdf` - Ingest PDF
- `POST /api/v1/ingest/url` - Ingest URL
- `POST /api/v1/ingest/text` - Ingest text
- `POST /api/v1/ingest/batch` - Batch ingestion

### Query
- `POST /api/v1/query` - Main query endpoint
- `POST /api/v1/query/conversational` - Conversational queries

### Search
- `POST /api/v1/search/vector` - Vector search
- `POST /api/v1/search/bm25` - BM25 search
- `POST /api/v1/search/hybrid` - Hybrid search with RRF
- `POST /api/v1/search/rerank` - Standalone reranking

### Memory
- `GET /api/v1/memory/short/{session_id}` - Short-term memory
- `GET /api/v1/memory/long/{user_id}` - Long-term memory
- `GET /api/v1/memory/episodic/{user_id}` - Episodic memory

## Architecture

```
User Query → Adaptive Router → [Vector + BM25] → RRF Fusion → Rerank → Gemini
                              ↓
                         Memory Layer
```

## Testing

```bash
pytest tests/ -v
```

## Deployment

See deployment guides in the main README.