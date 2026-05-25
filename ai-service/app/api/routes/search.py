"""
MemoraAI - API Routes: Search
Standalone search endpoints for vector, BM25, and hybrid search.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import structlog

from app.retrieval.vector_search import vector_searcher
from app.retrieval.bm25 import bm25_searcher
from app.retrieval.fusion import rrf_fusion
from app.retrieval.reranker import reranker
from app.embeddings.embedder import embedder
from app.security.validator import validator

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


class VectorSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    table: str = Field(default="chunks")


class BM25SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=100)
    table: str = Field(default="chunks")


class HybridSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=50)
    use_reranking: bool = Field(default=True)
    weights: Optional[dict] = Field(default=None)


class SearchResult(BaseModel):
    id: int
    content: str
    source: str
    score: float
    metadata: dict


@router.post("/vector")
async def vector_search(request: VectorSearchRequest):
    """Perform pure vector similarity search."""
    logger.info("vector_search_request", query=request.query[:50], top_k=request.top_k)

    validation = validator.validate_query(request.query)
    if not validation.valid:
        raise HTTPException(status_code=400, detail=validation.errors)

    try:
        query_vector = await embedder.embed_query(request.query)
        
        results = await vector_searcher.search(
            query_vector=query_vector,
            top_k=request.top_k,
            threshold=request.threshold,
            table=request.table,
        )

        return {
            "query": request.query,
            "method": "vector",
            "results": [
                {
                    "id": r.id,
                    "content": r.content,
                    "source": r.source,
                    "score": r.score,
                    "metadata": r.metadata,
                }
                for r in results
            ],
            "count": len(results),
        }

    except Exception as e:
        logger.error("vector_search_api_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bm25")
async def bm25_search(request: BM25SearchRequest):
    """Perform pure BM25 keyword search."""
    logger.info("bm25_search_request", query=request.query[:50], top_k=request.top_k)

    validation = validator.validate_query(request.query)
    if not validation.valid:
        raise HTTPException(status_code=400, detail=validation.errors)

    try:
        results = await bm25_searcher.search(
            query=request.query,
            top_k=request.top_k,
            table=request.table,
        )

        return {
            "query": request.query,
            "method": "bm25",
            "results": [
                {
                    "id": r.id,
                    "content": r.content,
                    "source": r.source,
                    "score": r.score,
                    "headline": r.headline,
                    "metadata": r.metadata,
                }
                for r in results
            ],
            "count": len(results),
        }

    except Exception as e:
        logger.error("bm25_search_api_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hybrid")
async def hybrid_search(request: HybridSearchRequest):
    """Perform hybrid search with RRF fusion."""
    logger.info("hybrid_search_request", query=request.query[:50], top_k=request.top_k)

    validation = validator.validate_query(request.query)
    if not validation.valid:
        raise HTTPException(status_code=400, detail=validation.errors)

    try:
        query_vector = await embedder.embed_query(request.query)

        vector_results = await vector_searcher.search(
            query_vector=query_vector,
            top_k=request.top_k * 2,
            table="chunks",
        )

        bm25_results = await bm25_searcher.search(
            query=request.query,
            top_k=request.top_k * 2,
            table="chunks",
        )

        fused_results = rrf_fusion.fuse(
            vector_results=vector_results,
            bm25_results=bm25_results,
        )

        if request.use_reranking and fused_results:
            docs = [{"content": r.content, "metadata": r.metadata} for r in fused_results]
            reranked = await reranker.rerank_with_metadata(
                query=request.query,
                documents=docs,
                top_k=request.top_k,
            )

            for idx, rerank_result in enumerate(reranked):
                if idx < len(fused_results):
                    fused_results[idx].rerank_score = rerank_result.get("rerank_score", 0)

            fused_results.sort(key=lambda x: x.rerank_score if x.rerank_score > 0 else x.fused_score, reverse=True)

        return {
            "query": request.query,
            "method": "hybrid",
            "fusion": "rrf",
            "results": [
                {
                    "id": r.id,
                    "content": r.content,
                    "source": r.source,
                    "fused_score": r.fused_score,
                    "vector_score": getattr(r, "vector_score", 0),
                    "bm25_score": getattr(r, "bm25_score", 0),
                    "rerank_score": r.rerank_score,
                    "metadata": r.metadata,
                }
                for r in fused_results[:request.top_k]
            ],
            "count": len(fused_results[:request.top_k]),
        }

    except Exception as e:
        logger.error("hybrid_search_api_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rerank")
async def rerank_documents(query: str, documents: list[dict], top_k: int = 5):
    """Rerank documents without retrieval."""
    logger.info("rerank_request", query=query[:50], doc_count=len(documents))

    if not documents:
        return {"query": query, "results": [], "count": 0}

    try:
        reranked = await reranker.rerank_with_metadata(
            query=query,
            documents=documents,
            top_k=top_k,
        )

        return {
            "query": query,
            "results": reranked,
            "count": len(reranked),
        }

    except Exception as e:
        logger.error("rerank_api_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))