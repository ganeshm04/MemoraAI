"""
MemoraAI - Prompt Templates
Grounded generation prompts with hallucination prevention.
"""

from typing import Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class PromptTemplate:
    """Prompt template with variables."""
    system: str
    user: str
    description: str


class PromptManager:
    """
    Manage prompt templates for grounded generation.
    
    Features:
    - Hallucination prevention rules
    - Source attribution
    - Context formatting
    - System prompts
    """

    GROUNDED_SYSTEM_PROMPT = """You are a helpful AI assistant with access to retrieved context.

IMPORTANT RULES:
1. Answer ONLY using the provided context
2. If context doesn't contain enough information, say "I don't have enough information to answer this question."
3. NEVER make up information or provide unsupported claims
4. Always cite sources when providing specific information
5. If you're uncertain, admit it

Response format:
- Start with direct answer
- Cite relevant context [Source X]
- If insufficient context, clearly state that"""

    RERANKING_SYSTEM_PROMPT = """You are a helpful AI assistant.

IMPORTANT RULES:
1. Answer based on your knowledge
2. Be clear about uncertainties
3. Provide accurate and helpful responses
4. If you don't know something, say so"""

    MEMORY_CONTEXT_PROMPT = """You have access to the user's memory:
- Short-term: {short_term}
- Long-term: {long_term}
- Episodic: {episodic}

Use this context to provide personalized responses."""

    def get_grounded_prompt(
        self,
        query: str,
        context_chunks: list[dict],
        include_memory: bool = False,
        memory_context: dict = None,
    ) -> tuple[str, str]:
        """
        Get grounded generation prompt.
        
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = self.GROUNDED_SYSTEM_PROMPT

        if include_memory and memory_context:
            system_prompt += "\n\n" + self.MEMORY_CONTEXT_PROMPT.format(
                short_term=memory_context.get("short_term", "No recent context"),
                long_term=memory_context.get("long_term", "No long-term memory"),
                episodic=memory_context.get("episodic", "No episodic memory"),
            )

        context_text = self._format_context(context_chunks)

        user_prompt = f"""Context:
{context_text}

Question: {query}

Answer:"""

        return system_prompt, user_prompt

    def get_conversational_prompt(
        self,
        query: str,
        conversation_history: list[dict],
    ) -> tuple[str, str]:
        """Get prompt for conversational queries."""
        system_prompt = self.RERANKING_SYSTEM_PROMPT

        history_text = ""
        if conversation_history:
            history_lines = []
            for msg in conversation_history[-10:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_lines.append(f"{role.capitalize()}: {content}")
            history_text = "\n".join(history_lines)

        user_prompt = f"""Conversation history:
{history_text}

Current question: {query}

Answer:"""

        return system_prompt, user_prompt

    def _format_context(self, chunks: list[dict]) -> str:
        """Format retrieved chunks as context string."""
        if not chunks:
            return "No relevant context available."

        parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("metadata", {}).get("source", "Unknown")
            content = chunk.get("content", "")
            score = chunk.get("fused_score", chunk.get("rerank_score", 0))
            
            parts.append(
                f"[Source {i}] (relevance: {score:.2f})\n"
                f"Source: {source}\n"
                f"Content: {content}"
            )

        return "\n\n---\n\n".join(parts)

    def get_summary_prompt(self, text: str, max_length: int = 200) -> tuple[str, str]:
        """Get prompt for text summarization."""
        system_prompt = "You are a helpful assistant that summarizes text accurately."

        user_prompt = f"""Summarize the following text in no more than {max_length} characters:

{text}

Summary:"""

        return system_prompt, user_prompt

    def get_memory_extraction_prompt(self, conversation: list[dict]) -> tuple[str, str]:
        """Get prompt for extracting memory-worthy information."""
        system_prompt = """You are an AI assistant that identifies important user information to remember.

Extract the following from the conversation:
1. User preferences and interests
2. Important facts about the user
3. Topics the user is interested in
4. Any explicit requests or requirements

Format the output as JSON with categories."""

        conversation_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in conversation
        ])

        user_prompt = f"""Extract key information from this conversation:

{conversation_text}

Extracted information (JSON):"""

        return system_prompt, user_prompt


class FallbackPrompts:
    """Safe fallback prompts for error cases."""

    RETRIEVAL_FAILED = """I apologize, but I encountered an issue retrieving information for your query. Please try again or rephrase your question."""

    INSUFFICIENT_CONTEXT = """I don't have enough information in the provided context to answer this question accurately. Could you provide more details or rephrase your question?"""

    GENERATION_ERROR = """I apologize, but I encountered an issue generating a response. Please try again."""

    RATE_LIMITED = """I apologize, but the service is currently experiencing high demand. Please wait a moment and try again."""


prompt_manager = PromptManager()
fallback_prompts = FallbackPrompts()