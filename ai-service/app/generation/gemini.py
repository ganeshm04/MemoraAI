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
    response_mime_type: Optional[str] = None


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
        self.model_name = "gemini-2.5-flash"
        self._current_key_idx = 0

    def _get_api_keys(self) -> list[str]:
        """Split and return the list of Gemini API keys configured."""
        raw_keys = config.settings.GEMINI_API_KEY
        if not raw_keys:
            raw_keys = config.settings.GOOGLE_API_KEY
        return [k.strip() for k in raw_keys.split(",") if k.strip()]

    def _configure_client(self, api_key: str):
        """Configure and return the genai client with the specified key context."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            return genai
        except ImportError:
            logger.error("google-generativeai_not_installed")
            raise

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResponse:
        """
        Generate text response with key fallback/rotation.
        
        Args:
            request: GenerationRequest with prompt and parameters
            
        Returns:
            GenerationResponse with generated text
        """
        import time
        from app.observability.metrics import generation_metrics

        full_prompt = self._build_prompt(request)

        logger.info(
            "generation_started",
            prompt_length=len(full_prompt),
            temperature=request.temperature,
        )

        keys = self._get_api_keys()
        if not keys:
            raise ValueError("No GEMINI_API_KEY or GOOGLE_API_KEY configured")

        start_time = time.perf_counter()
        last_error = None

        # Try every key in rotation, starting from self._current_key_idx
        for i in range(len(keys)):
            key_idx = (self._current_key_idx + i) % len(keys)
            current_key = keys[key_idx]

            try:
                client = self._configure_client(current_key)
                model = client.GenerativeModel(self.model_name)

                generation_config = {
                    "temperature": request.temperature,
                    "max_output_tokens": request.max_tokens,
                    "top_p": request.top_p,
                    "top_k": request.top_k,
                }
                if request.response_mime_type:
                    generation_config["response_mime_type"] = request.response_mime_type

                try:
                    response = model.generate_content(
                        full_prompt,
                        generation_config=generation_config,
                    )
                except Exception as e:
                    if request.response_mime_type and ("response_mime_type" in str(e) or "GenerationConfig" in str(e)):
                        logger.warning("response_mime_type_unsupported_by_sdk_retrying_without_it")
                        del generation_config["response_mime_type"]
                        response = model.generate_content(
                            full_prompt,
                            generation_config=generation_config,
                        )
                    else:
                        raise

                text = response.text
                finish_reason = str(response.finish_reason) if hasattr(response, 'finish_reason') else "COMPLETE"

                prompt_tokens = self._estimate_tokens(full_prompt)
                completion_tokens = self._estimate_tokens(text)
                total_tokens = prompt_tokens + completion_tokens

                duration_ms = (time.perf_counter() - start_time) * 1000.0
                generation_metrics.record_generation(duration_ms, total_tokens, finish_reason)

                logger.info(
                    "generation_completed",
                    response_length=len(text),
                    tokens_used=total_tokens,
                    finish_reason=finish_reason,
                    duration_ms=round(duration_ms, 2),
                    key_index=key_idx,
                )

                # Rotate to next key index for next request to distribute load evenly
                self._current_key_idx = (key_idx + 1) % len(keys)

                return GenerationResponse(
                    text=text,
                    model=self.model_name,
                    tokens_used=total_tokens,
                    finish_reason=finish_reason,
                    safety_ratings=getattr(response, 'safety_ratings', []),
                )

            except Exception as e:
                logger.warning(
                    "generation_attempt_failed_with_key",
                    key_index=key_idx,
                    error=str(e)[:150],
                )
                last_error = e

        logger.error("generation_all_keys_failed")
        if last_error:
            raise last_error
        raise ValueError("All Gemini API keys failed to generate content")

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
        Generate streaming response with key fallback/rotation.
        
        Args:
            request: GenerationRequest
            
        Yields:
            Text chunks as they become available
        """
        full_prompt = self._build_prompt(request)

        logger.info("streaming_generation_started", prompt_length=len(full_prompt))

        keys = self._get_api_keys()
        if not keys:
            raise ValueError("No GEMINI_API_KEY or GOOGLE_API_KEY configured")

        last_error = None
        # Try every key in rotation, starting from self._current_key_idx
        for i in range(len(keys)):
            key_idx = (self._current_key_idx + i) % len(keys)
            current_key = keys[key_idx]

            try:
                client = self._configure_client(current_key)
                model = client.GenerativeModel(self.model_name)

                generation_config = {
                    "temperature": request.temperature,
                    "max_output_tokens": request.max_tokens,
                    "top_p": request.top_p,
                    "top_k": request.top_k,
                }
                if request.response_mime_type:
                    generation_config["response_mime_type"] = request.response_mime_type

                try:
                    response = model.generate_content(
                        full_prompt,
                        generation_config=generation_config,
                        stream=True,
                    )
                except Exception as e:
                    if request.response_mime_type and ("response_mime_type" in str(e) or "GenerationConfig" in str(e)):
                        logger.warning("response_mime_type_unsupported_by_sdk_retrying_without_it")
                        del generation_config["response_mime_type"]
                        response = model.generate_content(
                            full_prompt,
                            generation_config=generation_config,
                            stream=True,
                        )
                    else:
                        raise

                # Try reading the first chunk to verify the stream connection with this key
                response_iterator = iter(response)
                first_chunk = next(response_iterator, None)

                # Successful read: update the active key index
                self._current_key_idx = key_idx

                if first_chunk and hasattr(first_chunk, "text") and first_chunk.text:
                    yield first_chunk.text

                # Yield subsequent chunks
                for chunk in response_iterator:
                    if chunk and hasattr(chunk, "text") and chunk.text:
                        yield chunk.text

                return

            except Exception as e:
                logger.warning(
                    "streaming_attempt_failed_with_key",
                    key_index=key_idx,
                    error=str(e)[:150],
                )
                last_error = e

        logger.error("streaming_generation_all_keys_failed")
        if last_error:
            raise last_error
        raise ValueError("All Gemini API keys failed to initiate streaming")

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