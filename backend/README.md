# MemoraAI Backend

Production-grade NestJS API orchestration service.

## Features

- **API Orchestration**: Routes requests to AI service
- **Rate Limiting**: Throttler-based protection
- **Security Middleware**: Helmet, CORS, HPP
- **Request Validation**: Zod + class-validator
- **Structured Logging**: Request/response logging
- **Error Handling**: Global exception filter
- **Swagger Documentation**: Auto-generated API docs

## Quick Start

### Local Development

```bash
# Install dependencies
npm install

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run in development mode
npm run start:dev

# Run in production
npm run start:prod
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

- `AI_SERVICE_URL`: AI service URL (default: http://localhost:8000)
- `AI_SERVICE_TIMEOUT`: Request timeout (default: 120000ms)
- `CORS_ORIGINS`: Allowed origins
- `RATE_LIMIT_TTL`: Rate limit window (ms)
- `RATE_LIMIT_LIMIT`: Max requests per window

## API Endpoints

### Health
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check

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
- `POST /api/v1/search/hybrid` - Hybrid search
- `POST /api/v1/search/rerank` - Reranking

### Memory
- `GET /api/v1/memory/short/:sessionId` - Short-term memory
- `POST /api/v1/memory/short` - Add to short-term memory
- `DELETE /api/v1/memory/short/:sessionId` - Clear short-term memory
- `GET /api/v1/memory/long/:userId` - Long-term memory
- `POST /api/v1/memory/long` - Store fact
- `DELETE /api/v1/memory/long/:userId/:key` - Delete fact
- `GET /api/v1/memory/episodic/:userId` - Episodic memory
- `POST /api/v1/memory/episodic` - Create episode
- `GET /api/v1/memory/stats/:userId` - Memory statistics

## Testing

```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# Coverage
npm run test:cov
```

## Architecture

```
Frontend → Backend (NestJS) → AI Service (FastAPI) → Database
```

## Deployment

See deployment guides in the main README.