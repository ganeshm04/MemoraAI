"""
MemoraAI - Gemini Client
Google Gemini 2.5 Flash integration for AI generation.
"""

from typing import Optional, AsyncIterator
from dataclasses import dataclass
from datetime import datetime
import structlog

from app.config import config

logger = structlog.get_logger(__name__)


@dataclass
class GenerationRequest:
    """Request for text generation."""
    prompt: str
    context: str = ""
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.95
    top_k: int = 40


@dataclass
class GenerationResponse:
    """Response from text generation."""
    text: str
    model: str
    tokens_used: int
    finish_reason: str
    safety_ratings: list = None


class GeminiClient:
    """
    Gemini 2.5 Flash client for AI generation.
    
    Features:
    - Streaming responses
    - Configurable parameters
    - Error handling and retries
    - Safety filtering
    """

    def __init__(self):
        self.api_key = config.settings.GEMINI_API_KEY
        self.model_name = "gemini-2.0-flash"
        self._client = None

    def _get_client(self):
        """Lazy load Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai
                logger.info("gemini_client_initialized", model=self.model_name)
            except ImportError:
                logger.error("google-generativeai_not_installed")
                raise
        return self._client

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResponse:
        """
        Generate text response.
        
        Args:
            request: GenerationRequest with prompt and parameters
            
        Returns:
            GenerationResponse with generated text
        """
        client = self._get_client()

        full_prompt = self._build_prompt(request)

        logger.info(
            "generation_started",
            prompt_length=len(full_prompt),
            temperature=request.temperature,
        )

        for attempt in range(3):
            try:
                model = client.GenerativeModel(self.model_name)

                generation_config = {
                    "temperature": request.temperature,
                    "max_output_tokens": request.max_tokens,
                    "top_p": request.top_p,
                    "top_k": request.top_k,
                }

                response = model.generate_content(
                    full_prompt,
                    generation_config=generation_config,
                )

                text = response.text
                finish_reason = str(response.finish_reason) if hasattr(response, 'finish_reason') else "COMPLETE"

                prompt_tokens = self._estimate_tokens(full_prompt)
                completion_tokens = self._estimate_tokens(text)
                total_tokens = prompt_tokens + completion_tokens

                logger.info(
                    "generation_completed",
                    response_length=len(text),
                    tokens_used=total_tokens,
                    finish_reason=finish_reason,
                )

                return GenerationResponse(
                    text=text,
                    model=self.model_name,
                    tokens_used=total_tokens,
                    finish_reason=finish_reason,
                    safety_ratings=getattr(response, 'safety_ratings', []),
                )

            except Exception as e:
                logger.warning(
                    "generation_attempt_failed",
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt == 2:
                    logger.error("generation_all_attempts_failed")
                    raise

    async def generate_with_context(
        self,
        prompt: str,
        context_chunks: list[dict],
        system_prompt: str = None,
    ) -> GenerationResponse:
        """
        Generate response with retrieved context.
        
        Args:
            prompt: User prompt
            context_chunks: Retrieved context chunks
            system_prompt: Optional system prompt
            
        Returns:
            GenerationResponse
        """
        context = self._format_context(context_chunks)

        request = GenerationRequest(
            prompt=prompt,
            context=context,
            system_prompt=system_prompt or self._get_default_system_prompt(),
        )

        return await self.generate(request)

    async def stream_generate(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[str]:
        """
        Generate streaming response.
        
        Args:
            request: GenerationRequest
            
        Yields:
            Text chunks as they become available
        """
        client = self._get_client()

        full_prompt = self._build_prompt(request)

        logger.info("streaming_generation_started", prompt_length=len(full_prompt))

        try:
            model = client.GenerativeModel(self.model_name)

            generation_config = {
                "temperature": request.temperature,
                "max_output_tokens": request.max_tokens,
                "top_p": request.top_p,
                "top_k": request.top_k,
            }

            response = model.generate_content(
                full_prompt,
                generation_config=generation_config,
                stream=True,
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error("streaming_generation_failed", error=str(e))
            raise

    def _build_prompt(self, request: GenerationRequest) -> str:
        """Build full prompt with context."""
        parts = []

        if request.system_prompt:
            parts.append(f"System: {request.system_prompt}")

        if request.context:
            parts.append(f"Context:\n{request.context}")

        parts.append(f"User: {request.prompt}")
        parts.append("Assistant:")

        return "\n\n".join(parts)

    def _format_context(self, chunks: list[dict]) -> str:
        """Format retrieved chunks as context."""
        if not chunks:
            return "No relevant context available."

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("metadata", {}).get("source", "Unknown")
            content = chunk.get("content", "")
            context_parts.append(f"[Source {i}] {source}:\n{content}\n")

        return "\n---\n".join(context_parts)

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for grounded responses."""
        return """You are a helpful AI assistant. Answer questions using ONLY the provided context. 
If the context doesn't contain enough information, say "I don't have enough information to answer this question."
Do not make up information or provide unsupported claims.
Always cite relevant information from the context when answering."""

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (approximate)."""
        return int(len(text.split()) * 1.3)


class SafeFallbackClient(GeminiClient):
    """Gemini client with safe fallback responses."""

    async def generate_with_fallback(
        self,
        request: GenerationRequest,
    ) -> GenerationResponse:
        """
        Generate with fallback if primary fails.
        
        Args:
            request: GenerationRequest
            
        Returns:
            GenerationResponse or safe fallback
        """
        try:
            return await self.generate(request)
        except Exception as e:
            logger.warning("generation_failed_using_fallback", error=str(e))
            return GenerationResponse(
                text="I apologize, but I encountered an issue generating a response. Please try again or rephrase your question.",
                model="fallback",
                tokens_used=0,
                finish_reason="FALLBACK",
            )


gemini_client = GeminiClient()
safe_gemini_client = SafeFallbackClient()