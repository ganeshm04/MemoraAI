"""
MemoraAI - API Routes: Memory
Memory management endpoints for short-term, long-term, and episodic memory.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import structlog

from app.memory.short_term import short_term_memory, ConversationContext
from app.memory.long_term import long_term_memory, UserFact
from app.memory.episodic import episodic_memory, Episode
from app.generation.gemini import safe_gemini_client, GenerationRequest
from app.prompts.templates import prompt_manager
from app.api.routes.query import extract_and_store_facts

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/memory", tags=["memory"])


class AddMemoryRequest(BaseModel):
    session_id: str
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    metadata: Optional[dict] = None


class GetMemoryRequest(BaseModel):
    session_id: str
    limit: int = Field(default=20, ge=1, le=100)


class StoreFactRequest(BaseModel):
    user_id: str
    key: str
    value: str
    category: str = "general"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str = "conversation"


class GetFactsRequest(BaseModel):
    user_id: str
    category: Optional[str] = None


class CreateEpisodeRequest(BaseModel):
    user_id: str
    session_id: str
    summary: str
    key_topics: list[str] = []
    important_facts: list[str] = []
    sentiment: str = "neutral"
    duration_minutes: int = 0
    message_count: int = 0


class SummarizeSessionRequest(BaseModel):
    user_id: str
    session_id: str


@router.get("/short/{session_id}")
async def get_short_term_memory(session_id: str, limit: int = 20):
    """Get short-term memory for a session."""
    logger.info("stm_get_request", session_id=session_id)

    try:
        messages = await short_term_memory.get_conversation(session_id, limit=limit)
        
        return {
            "session_id": session_id,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "token_count": m.token_count,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ],
            "count": len(messages),
        }

    except Exception as e:
        logger.error("stm_get_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/short/add")
async def add_short_term_memory(request: AddMemoryRequest):
    """Add message to short-term memory."""
    logger.info("stm_add_request", session_id=request.session_id, role=request.role)

    try:
        message_id = await short_term_memory.add_message(
            session_id=request.session_id,
            role=request.role,
            content=request.content,
            metadata=request.metadata,
        )

        return {"success": True, "message_id": message_id}

    except Exception as e:
        logger.error("stm_add_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/short/{session_id}")
async def clear_short_term_memory(session_id: str):
    """Clear short-term memory for a session."""
    logger.info("stm_clear_request", session_id=session_id)

    try:
        await short_term_memory.clear_session(session_id)
        return {"success": True, "session_id": session_id}

    except Exception as e:
        logger.error("stm_clear_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/long/{user_id}")
async def get_long_term_memory(user_id: str, category: str = None):
    """Get long-term memory facts for a user."""
    logger.info("ltm_get_request", user_id=user_id)

    try:
        facts = await long_term_memory.get_all_facts(user_id, category=category)

        return {
            "user_id": user_id,
            "facts": [
                {
                    "id": f.id,
                    "key": f.key,
                    "value": f.value,
                    "category": f.category,
                    "confidence": f.confidence,
                    "source": f.source,
                    "created_at": f.created_at.isoformat(),
                    "updated_at": f.updated_at.isoformat(),
                }
                for f in facts
            ],
            "count": len(facts),
        }

    except Exception as e:
        logger.error("ltm_get_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/long/fact")
async def store_long_term_fact(request: StoreFactRequest):
    """Store a fact in long-term memory."""
    logger.info("ltm_store_request", user_id=request.user_id, key=request.key)

    try:
        fact_id = await long_term_memory.store_fact(
            user_id=request.user_id,
            key=request.key,
            value=request.value,
            category=request.category,
            confidence=request.confidence,
            source=request.source,
        )

        return {"success": True, "fact_id": fact_id}

    except Exception as e:
        logger.error("ltm_store_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/long/{user_id}/{key}")
async def delete_long_term_fact(user_id: str, key: str):
    """Delete a fact from long-term memory."""
    logger.info("ltm_delete_request", user_id=user_id, key=key)

    try:
        success = await long_term_memory.delete_fact(user_id, key)
        return {"success": success, "user_id": user_id, "key": key}

    except Exception as e:
        logger.error("ltm_delete_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/episodic/{user_id}")
async def get_episodic_memory(user_id: str, limit: int = 10, days: int = 30):
    """Get recent episodic memories for a user."""
    logger.info("em_get_request", user_id=user_id)

    try:
        episodes = await episodic_memory.get_recent_episodes(user_id, limit=limit, days=days)

        return {
            "user_id": user_id,
            "episodes": [
                {
                    "id": e.id,
                    "session_id": e.session_id,
                    "summary": e.summary,
                    "key_topics": e.key_topics,
                    "important_facts": e.important_facts,
                    "sentiment": e.sentiment,
                    "duration_minutes": e.duration_minutes,
                    "message_count": e.message_count,
                    "created_at": e.created_at.isoformat(),
                }
                for e in episodes
            ],
            "count": len(episodes),
        }

    except Exception as e:
        logger.error("em_get_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/episodic")
async def create_episode(request: CreateEpisodeRequest):
    """Create a new episodic memory."""
    logger.info("em_create_request", user_id=request.user_id, session_id=request.session_id)

    try:
        episode_id = await episodic_memory.create_episode(
            user_id=request.user_id,
            session_id=request.session_id,
            summary=request.summary,
            key_topics=request.key_topics,
            important_facts=request.important_facts,
            sentiment=request.sentiment,
            duration_minutes=request.duration_minutes,
            message_count=request.message_count,
        )

        return {"success": True, "episode_id": episode_id}

    except Exception as e:
        logger.error("em_create_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/episodic/summarize")
async def summarize_session(request: SummarizeSessionRequest):
    """Automatically extract facts and summarize a session into episodic memory."""
    logger.info("em_summarize_request", user_id=request.user_id, session_id=request.session_id)

    try:
        # 1. Fetch conversation history
        messages = await short_term_memory.get_conversation(request.session_id)
        if not messages:
            logger.info("em_summarize_skipped_empty_conversation", session_id=request.session_id)
            return {"success": True, "message": "No conversation history to summarize"}

        # 2. Extract long-term facts from the conversation
        try:
            logger.info("em_summarize_extracting_ltm_facts", session_id=request.session_id)
            await extract_and_store_facts(request.user_id, messages)
        except Exception as e:
            logger.warning("em_summarize_ltm_extraction_failed", error=str(e))

        # 3. Generate episodic summary
        conversation = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        system_prompt, user_prompt = prompt_manager.get_episodic_summary_prompt(conversation)
        gen_request = GenerationRequest(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=1024,
            response_mime_type="application/json",
        )

        generation = await safe_gemini_client.generate(gen_request)

        import json
        import re
        summary_data = {}
        try:
            text = generation.text.strip()
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

            summary_data = json.loads(text)
        except Exception as e:
            logger.warning("em_summarize_json_parse_failed", error=str(e), text=generation.text)
            summary_data = {
                "summary": f"Interaction session of {len(messages)} messages.",
                "key_topics": [],
                "important_facts": [],
                "sentiment": "neutral"
            }

        summary = summary_data.get("summary", f"Session with {len(messages)} messages.")
        key_topics = summary_data.get("key_topics", [])
        important_facts = summary_data.get("important_facts", [])
        sentiment = summary_data.get("sentiment", "neutral")

        # Estimate duration
        duration_minutes = 0
        if len(messages) >= 2:
            first_msg = messages[0]
            last_msg = messages[-1]
            if first_msg.created_at and last_msg.created_at:
                delta = last_msg.created_at - first_msg.created_at
                duration_minutes = max(1, int(delta.total_seconds() / 60))

        # 4. Create episodic memory record
        episode_id = await episodic_memory.create_episode(
            user_id=request.user_id,
            session_id=request.session_id,
            summary=summary,
            key_topics=key_topics,
            important_facts=important_facts,
            sentiment=sentiment,
            duration_minutes=duration_minutes,
            message_count=len(messages),
        )

        return {"success": True, "episode_id": episode_id}

    except Exception as e:
        logger.error("em_summarize_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{user_id}")
async def get_memory_stats(user_id: str):
    """Get aggregated memory statistics for a user."""
    logger.info("memory_stats_request", user_id=user_id)

    try:
        episodic_stats = await episodic_memory.get_interaction_stats(user_id)
        
        long_term_facts = await long_term_memory.get_all_facts(user_id)
        
        return {
            "user_id": user_id,
            "episodic": episodic_stats,
            "long_term_facts_count": len(long_term_facts),
        }

    except Exception as e:
        logger.error("memory_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))