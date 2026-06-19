"""
MemoraAI - API Routes: Query
Main query endpoint with retrieval and generation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import structlog

from app.core.router import router as query_router, QueryType
from app.retrieval.pipeline import retrieval_pipeline, adaptive_retrieval
from app.generation.gemini import safe_gemini_client, GenerationRequest
from app.memory.short_term import short_term_memory, ConversationContext
from app.memory.long_term import long_term_memory
from app.memory.episodic import episodic_memory
from app.security.sanitizer import sanitizer
from app.security.validator import validator
from app.prompts.templates import prompt_manager
from app.config import config

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/query", tags=["query"])

MEMORY_EXTRACT_INTERVAL = 5  # Extract facts every N messages


class QueryRequest(BaseModel):
    query: str = Field(..., description="User query")
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(default="default-user", description="User identifier")
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
    5. Automatic memory extraction
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

        # Filter by confidence threshold
        threshold = config.settings.SIMILARITY_THRESHOLD
        retrieval_results = [
            r for r in retrieval_results
            if r.vector_score >= threshold or r.bm25_score > 0 or (r.rerank_score and r.rerank_score >= 0.0)
        ]

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

    # Build memory context
    memory_context = {}
    if request.use_memory:
        # Short-term memory
        context_window = await short_term_memory.get_context_window(request.session_id)
        memory_context["short_term"] = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in context_window.messages[-5:]
        ])

        # Long-term memory
        if request.user_id:
            try:
                facts = await long_term_memory.get_all_facts(request.user_id)
                if facts:
                    memory_context["long_term"] = "\n".join([
                        f"- {f.key}: {f.value} (confidence: {f.confidence:.0%})"
                        for f in facts[:10]
                    ])
            except Exception as e:
                logger.warning("long_term_memory_fetch_failed", error=str(e))

        # Episodic memory
        if request.user_id:
            try:
                episodes = await episodic_memory.get_recent_episodes(request.user_id, limit=3)
                if episodes:
                    memory_context["episodic"] = "\n".join([
                        f"- Session ({e.created_at.strftime('%Y-%m-%d') if e.created_at else 'unknown'}): {e.summary}"
                        for e in episodes
                    ])
            except Exception as e:
                logger.warning("episodic_memory_fetch_failed", error=str(e))

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

        # Trigger memory extraction periodically
        try:
            all_messages = await short_term_memory.get_conversation(request.session_id)
            if len(all_messages) > 0 and len(all_messages) % MEMORY_EXTRACT_INTERVAL == 0 and request.user_id:
                await extract_and_store_facts(request.user_id, all_messages[-MEMORY_EXTRACT_INTERVAL:])
        except Exception as e:
            logger.warning("memory_extraction_skipped", error=str(e))

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


async def extract_and_store_facts(user_id: str, messages: list):
    """Extract facts from conversation and store in long-term memory."""
    try:
        conversation = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        system_prompt, user_prompt = prompt_manager.get_memory_extraction_prompt(conversation)
        gen_request = GenerationRequest(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=1024,
            response_mime_type="application/json",
        )

        result = await safe_gemini_client.generate(gen_request)

        # Try to parse JSON from the response
        import json
        import re
        try:
            # Try to extract JSON from the response text
            text = result.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            text = text.strip()

            # Robustly isolate JSON block matching outer braces
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)

            facts = json.loads(text)

            if isinstance(facts, dict):
                for category, items in facts.items():
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                key = item.get("key", item.get("fact", str(item)))
                                value = item.get("value", item.get("detail", str(item)))
                            else:
                                key = str(item)[:50]
                                value = str(item)
                            await long_term_memory.store_fact(
                                user_id=user_id,
                                key=str(key)[:100],
                                value=str(value)[:500],
                                category=str(category),
                                confidence=0.7,
                                source="auto_extraction",
                            )
                    elif isinstance(items, str):
                        await long_term_memory.store_fact(
                            user_id=user_id,
                            key=str(category)[:100],
                            value=str(items)[:500],
                            category="general",
                            confidence=0.7,
                            source="auto_extraction",
                        )

            logger.info("memory_facts_extracted", user_id=user_id)

        except json.JSONDecodeError:
            logger.warning("memory_extraction_json_parse_failed", raw_text=result.text)

    except Exception as e:
        logger.warning("memory_extraction_failed", error=str(e))