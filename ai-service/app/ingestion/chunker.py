"""
MemoraAI - Token-Based Chunker
Semantic chunking with configurable size and overlap.
"""

import re
from typing import Optional
import structlog

from app.config import config

logger = structlog.get_logger(__name__)


class Tokenizer:
    """Simple tokenizer for counting tokens (approximate word-based)."""

    def __init__(self):
        self._token_pattern = re.compile(r"\b\w+\b|[.,!?;:'\"()\[\]{}]")

    def count_tokens(self, text: str) -> int:
        """Count approximate tokens in text."""
        tokens = self._token_pattern.findall(text)
        return len(tokens)

    def tokenize(self, text: str) -> list[str]:
        """Split text into tokens."""
        return self._token_pattern.findall(text)

    def split_tokens(self, text: str, max_tokens: int, overlap_tokens: int = 0) -> list[str]:
        """
        Split text into token-based chunks with overlap.
        
        Args:
            text: Text to split
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Number of tokens to overlap between chunks
            
        Returns:
            List of text chunks
        """
        words = text.split()
        if not words:
            return []

        chunks = []
        start = 0

        while start < len(words):
            end = start + max_tokens
            chunk_words = words[start:end]
            
            if chunk_words:
                chunks.append(" ".join(chunk_words))

            if overlap_tokens > 0 and end < len(words):
                start = end - overlap_tokens
            else:
                break

        return chunks


class ChunkMetadata:
    """Metadata for a chunk."""

    def __init__(
        self,
        document_id: int,
        chunk_index: int,
        total_chunks: int,
        source: str,
        chunk_size: int,
        token_count: int,
        custom_config: Optional[dict] = None,
    ):
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.total_chunks = total_chunks
        self.source = source
        self.chunk_size = chunk_size
        self.token_count = token_count
        self.custom_config = custom_config or {}

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "source": self.source,
            "chunk_size": self.chunk_size,
            "token_count": self.token_count,
            **self.custom_config,
        }


class Chunker:
    """
    Token-based document chunker with semantic preservation.
    
    Features:
    - Token-based chunking (not character-based)
    - Configurable chunk size and overlap
    - Document-level override support
    - Metadata preservation
    """

    def __init__(
        self,
        default_chunk_size: int = None,
        default_overlap: int = None,
    ):
        self.default_chunk_size = default_chunk_size or config.retrieval.chunk_size
        self.default_overlap = default_overlap or config.retrieval.chunk_overlap
        self.tokenizer = Tokenizer()

    def chunk_text(
        self,
        text: str,
        document_id: int,
        source: str,
        chunk_size: int = None,
        overlap: int = None,
        custom_config: Optional[dict] = None,
    ) -> list[tuple[str, ChunkMetadata]]:
        """
        Split text into token-based chunks with metadata.
        
        Args:
            text: Text to chunk
            document_id: ID of the parent document
            source: Source identifier (url, filename, etc.)
            chunk_size: Override default chunk size
            overlap: Override default overlap
            custom_config: Additional metadata configuration
            
        Returns:
            List of (chunk_text, metadata) tuples
        """
        chunk_size = chunk_size or self.default_chunk_size
        overlap = overlap or self.default_overlap

        logger.info(
            "chunking_started",
            document_id=document_id,
            text_length=len(text),
            chunk_size=chunk_size,
            overlap=overlap,
        )

        text = self._clean_text(text)
        
        if not text.strip():
            logger.warning("empty_text_after_cleaning", document_id=document_id)
            return []

        tokens = self.tokenizer.tokenize(text)
        total_tokens = len(tokens)
        total_chunks = max(1, (total_tokens + chunk_size - 1) // chunk_size)

        chunks = []
        start_token = 0
        chunk_index = 0

        while start_token < total_tokens:
            end_token = min(start_token + chunk_size, total_tokens)
            chunk_tokens = tokens[start_token:end_token]
            chunk_text = " ".join(chunk_tokens)

            if chunk_text.strip():
                metadata = ChunkMetadata(
                    document_id=document_id,
                    chunk_index=chunk_index,
                    total_chunks=total_chunks,
                    source=source,
                    chunk_size=len(chunk_text),
                    token_count=len(chunk_tokens),
                    custom_config=custom_config,
                )
                chunks.append((chunk_text, metadata))
                chunk_index += 1

            if end_token >= total_tokens:
                break

            start_token = end_token - overlap

        logger.info(
            "chunking_completed",
            document_id=document_id,
            total_chunks=len(chunks),
            total_tokens=total_tokens,
        )

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for chunking."""
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" ?\.{3,} ?", " ", text)
        text = text.strip()
        return text

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return self.tokenizer.count_tokens(text)

    def validate_config(self, chunk_size: int, overlap: int) -> list[str]:
        """Validate chunking configuration."""
        errors = []
        
        if chunk_size < 100:
            errors.append(f"Chunk size {chunk_size} is too small (minimum: 100)")
        if chunk_size > 2000:
            errors.append(f"Chunk size {chunk_size} exceeds maximum (2000)")
        if overlap < 0:
            errors.append("Overlap cannot be negative")
        if overlap >= chunk_size:
            errors.append(f"Overlap {overlap} must be less than chunk size {chunk_size}")
            
        return errors


def create_chunker(
    chunk_size: int = None,
    overlap: int = None,
) -> Chunker:
    """Factory function to create a configured chunker."""
    return Chunker(
        default_chunk_size=chunk_size,
        default_overlap=overlap,
    )


chunker = Chunker()