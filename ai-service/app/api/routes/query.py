"""
MemoraAI - API Routes: Query
Main query endpoint with retrieval and generation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, list
import structlog

from app.core.router import router as query_router, QueryType
from app.retrieval.pipeline import retrieval_pipeline, adaptive_retrieval
from app.generation.gemini import safe_gemini_client, GenerationRequest
from app.memory.short_term import short_term_memory, ConversationContext
from app.security.sanitizer import sanitizer
from app.security.validator import validator
from app.prompts.templates import prompt_manager

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    query: str = Field(..., description="User query")
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    use_memory: bool = Field(default=True, description="Include memory context")
    use_reranking: bool = Field(default=True, description="Use reranking")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=8192)


class RetrievedChunk(BaseModel):
    id: int
    content: str
    source: str
    fused_score: float
    vector_score: float = 0.0
    bm25_score: float = 0.0
    rerank_score: float = 0.0


class QueryResponse(BaseModel):
    response: str
    session_id: str
    query_type: str
    chunks: list[RetrievedChunk]
    tokens_used: int
    sources: list[str]


@router.post("/", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Main query endpoint with adaptive retrieval and generation.
    
    Pipeline:
    1. Query routing (classify query type)
    2. Retrieval (if needed based on query type)
    3. Memory context (if enabled)
    4. Generation with grounded context
    """
    logger.info("query_request_received", session_id=request.session_id, query=request.query[:50])

    validation = validator.validate_query(request.query)
    if not validation.valid:
        raise HTTPException(status_code=400, detail=validation.errors)

    sanitized_query = sanitizer.sanitize_query(request.query)

    routing = query_router.route(sanitized_query)
    logger.info("query_routed", strategy=routing.strategy, query_type=routing.query_type.value)

    await short_term_memory.add_message(
        session_id=request.session_id,
        role="user",
        content=sanitized_query,
    )

    chunks = []
    if routing.requires_retrieval:
        retrieval_results = await retrieval_pipeline.search(
            query=sanitized_query,
            use_reranking=request.use_reranking,
        )

        chunks = [
            RetrievedChunk(
                id=r.id,
                content=r.content,
                source=r.source,
                fused_score=r.fused_score,
                vector_score=r.vector_score,
                bm25_score=r.bm25_score,
                rerank_score=r.rerank_score,
            )
            for r in retrieval_results
        ]

    memory_context = {}
    if request.use_memory:
        context_window = await short_term_memory.get_context_window(request.session_id)
        memory_context["short_term"] = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in context_window.messages[-5:]
        ])

    context_chunks = [
        {"content": c.content, "metadata": {"source": c.source}}
        for c in chunks
    ]

    try:
        system_prompt, user_prompt = prompt_manager.get_grounded_prompt(
            query=sanitized_query,
            context_chunks=context_chunks,
            include_memory=request.use_memory,
            memory_context=memory_context if request.use_memory else None,
        )

        gen_request = GenerationRequest(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        generation = await safe_gemini_client.generate(gen_request)

        await short_term_memory.add_message(
            session_id=request.session_id,
            role="assistant",
            content=generation.text,
            token_count=generation.tokens_used,
        )

        sources = list(set([c.source for c in chunks if c.source]))

        logger.info(
            "query_completed",
            session_id=request.session_id,
            response_length=len(generation.text),
            chunks_used=len(chunks),
            tokens_used=generation.tokens_used,
        )

        return QueryResponse(
            response=generation.text,
            session_id=request.session_id,
            query_type=routing.query_type.value,
            chunks=chunks,
            tokens_used=generation.tokens_used,
            sources=sources,
        )

    except Exception as e:
        logger.error("query_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversational")
async def conversational_query(request: QueryRequest):
    """Handle conversational queries without retrieval."""
    logger.info("conversational_query_request", session_id=request.session_id)

    validation = validator.validate_query(request.query)
    if not validation.valid:
        raise HTTPException(status_code=400, detail=validation.errors)

    sanitized_query = sanitizer.sanitize_query(request.query)

    context_window = await short_term_memory.get_context_window(request.session_id)
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in context_window.messages
    ]

    try:
        system_prompt, user_prompt = prompt_manager.get_conversational_prompt(
            query=sanitized_query,
            conversation_history=conversation_history,
        )

        gen_request = GenerationRequest(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        generation = await safe_gemini_client.generate(gen_request)

        await short_term_memory.add_message(
            session_id=request.session_id,
            role="user",
            content=sanitized_query,
        )
        await short_term_memory.add_message(
            session_id=request.session_id,
            role="assistant",
            content=generation.text,
            token_count=generation.tokens_used,
        )

        return {
            "response": generation.text,
            "session_id": request.session_id,
            "query_type": "conversational",
            "tokens_used": generation.tokens_used,
        }

    except Exception as e:
        logger.error("conversational_query_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))