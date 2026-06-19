"""
MemoraAI - Ingestion Processor
Unified ingestion pipeline for PDF, URL, and text sources.
"""

import json
import structlog
from typing import Optional, Literal
from dataclasses import dataclass, field

from app.ingestion.pdf_parser import pdf_parser
from app.ingestion.url_scraper import url_scraper
from app.ingestion.text_cleaner import text_cleaner, content_filter
from app.ingestion.chunker import chunker, Chunker, ChunkMetadata
from app.embeddings.embedder import embedder
from db.connection import db, vector_store

logger = structlog.get_logger(__name__)


@dataclass
class IngestionResult:
    """Result of an ingestion operation."""
    success: bool
    document_id: Optional[int] = None
    source: str = ""
    source_type: str = ""
    chunks_created: int = 0
    text_length: int = 0
    errors: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class IngestionConfig:
    """Configuration for ingestion pipeline."""
    chunk_size: int = 700
    chunk_overlap: int = 100
    clean_text: bool = True
    validate_content: bool = True


class IngestionProcessor:
    """
    Unified document ingestion processor.
    
    Handles:
    - PDF files
    - URLs
    - Text notes
    - Content validation
    - Chunking
    - Embedding generation
    - Database storage
    """

    def __init__(self, config: Optional[IngestionConfig] = None):
        self.config = config or IngestionConfig()
        self.chunker = Chunker(
            default_chunk_size=self.config.chunk_size,
            default_overlap=self.config.chunk_overlap,
        )

    async def ingest_pdf(self, file_path: str, metadata: Optional[dict] = None) -> IngestionResult:
        """
        Ingest PDF document.
        
        Args:
            file_path: Path to PDF file
            metadata: Additional metadata
            
        Returns:
            IngestionResult with status and details
        """
        logger.info("pdf_ingestion_started", file_path=file_path)
        
        try:
            text = await pdf_parser.extract_text(file_path)
            text = self._process_text(text)
            
            # Use original filename as the source identifier and title if available
            original_filename = metadata.get("filename") if metadata else None
            db_source = original_filename or file_path
            
            chunks = self.chunker.chunk_text(
                text=text,
                document_id=0,
                source=db_source,
                custom_config={"file_path": file_path, **(metadata or {})},
            )
            
            doc_id = await self._persist_chunks(
                chunks=chunks,
                source=db_source,
                source_type="pdf",
                title=original_filename or (metadata.get("title") if metadata else None) or file_path,
                metadata=metadata,
            )
            
            return IngestionResult(
                success=True,
                document_id=doc_id,
                source=db_source,
                source_type="pdf",
                chunks_created=len(chunks),
                text_length=len(text),
                metadata={
                    "file_path": file_path,
                    **(metadata or {}),
                },
            )

        except Exception as e:
            logger.error("pdf_ingestion_failed", file_path=file_path, error=str(e))
            return IngestionResult(
                success=False,
                source=file_path,
                source_type="pdf",
                errors=[str(e)],
            )

    async def ingest_url(self, url: str, metadata: Optional[dict] = None) -> IngestionResult:
        """
        Ingest content from URL.
        
        Args:
            url: URL to scrape
            metadata: Additional metadata
            
        Returns:
            IngestionResult with status and details
        """
        logger.info("url_ingestion_started", url=url)
        
        try:
            text = await url_scraper.scrape(url)
            text = self._process_text(text)
            
            url_metadata = await url_scraper.get_metadata(url)
            merged_metadata = {**url_metadata, **(metadata or {})}
            
            chunks = self.chunker.chunk_text(
                text=text,
                document_id=0,
                source=url,
                custom_config={"url": url, **merged_metadata},
            )
            
            doc_id = await self._persist_chunks(
                chunks=chunks,
                source=url,
                source_type="url",
                title=merged_metadata.get("title"),
                metadata=merged_metadata,
            )
            
            return IngestionResult(
                success=True,
                document_id=doc_id,
                source=url,
                source_type="url",
                chunks_created=len(chunks),
                text_length=len(text),
                metadata=merged_metadata,
            )

        except Exception as e:
            logger.error("url_ingestion_failed", url=url, error=str(e))
            return IngestionResult(
                success=False,
                source=url,
                source_type="url",
                errors=[str(e)],
            )

    async def ingest_text(
        self,
        text: str,
        source: str = "text_input",
        metadata: Optional[dict] = None,
    ) -> IngestionResult:
        """
        Ingest plain text content.
        
        Args:
            text: Text content to ingest
            source: Source identifier
            metadata: Additional metadata
            
        Returns:
            IngestionResult with status and details
        """
        logger.info("text_ingestion_started", source=source, text_length=len(text))
        
        try:
            text = self._process_text(text)
            
            chunks = self.chunker.chunk_text(
                text=text,
                document_id=0,
                source=source,
                custom_config=metadata or {},
            )
            
            doc_id = await self._persist_chunks(
                chunks=chunks,
                source=source,
                source_type="text",
                title=metadata.get("title") if metadata else None,
                metadata=metadata,
            )
            
            return IngestionResult(
                success=True,
                document_id=doc_id,
                source=source,
                source_type="text",
                chunks_created=len(chunks),
                text_length=len(text),
                metadata=metadata or {},
            )

        except Exception as e:
            logger.error("text_ingestion_failed", source=source, error=str(e))
            return IngestionResult(
                success=False,
                source=source,
                source_type="text",
                errors=[str(e)],
            )

    async def ingest_batch(
        self,
        sources: list[dict],
    ) -> list[IngestionResult]:
        """
        Ingest multiple sources in batch.
        
        Args:
            sources: List of source dicts with 'type' and 'content'
            
        Returns:
            List of IngestionResult
        """
        results = []
        
        for source in sources:
            source_type = source.get("type", "text")
            content = source.get("content")
            
            if source_type == "pdf":
                result = await self.ingest_pdf(content, source.get("metadata"))
            elif source_type == "url":
                result = await self.ingest_url(content, source.get("metadata"))
            else:
                result = await self.ingest_text(content, source.get("source", "batch"), source.get("metadata"))
            
            results.append(result)
        
        logger.info("batch_ingestion_completed", total=len(sources), successful=sum(1 for r in results if r.success))
        
        return results

    async def _persist_chunks(
        self,
        chunks: list[tuple[str, ChunkMetadata]],
        source: str,
        source_type: str,
        title: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> int:
        """Persist chunks with embeddings to the database."""
        if not chunks:
            logger.warning("no_chunks_to_persist", source=source)
            return 0

        try:
            doc_id = await db.fetchval(
                """INSERT INTO documents (source, source_type, title, metadata)
                   VALUES ($1, $2, $3, $4) RETURNING id""",
                source, source_type, title or source,
                json.dumps(metadata or {}),
            )

            chunk_texts = [c[0] for c in chunks]
            embeddings = await embedder.embed_texts(chunk_texts)

            for (chunk_text, chunk_meta), embedding in zip(chunks, embeddings):
                meta = chunk_meta.to_dict()
                vector_str = f"[{','.join(str(v) for v in embedding)}]"
                await db.execute(
                    """INSERT INTO chunks (document_id, content, embedding, metadata, chunk_index, total_chunks, token_count)
                       VALUES ($1, $2, $3::vector, $4, $5, $6, $7)""",
                    doc_id, chunk_text, vector_str,
                    json.dumps(meta),
                    chunk_meta.chunk_index,
                    chunk_meta.total_chunks,
                    chunk_meta.token_count,
                )

            await db.execute("UPDATE documents SET indexed = TRUE WHERE id = $1", doc_id)

            logger.info(
                "chunks_persisted",
                document_id=doc_id,
                chunks_count=len(chunks),
                source=source,
            )
            return doc_id

        except Exception as e:
            logger.error("chunk_persistence_failed", source=source, error=str(e))
            raise

    def _process_text(self, text: str) -> str:
        """Process and validate text content."""
        if self.config.clean_text:
            text = text_cleaner.clean(text)
        
        if self.config.validate_content:
            if not content_filter.is_valid(text):
                logger.warning("content_validation_failed", text_length=len(text))
        
        return text

    def get_chunking_config(self) -> dict:
        """Get current chunking configuration."""
        return {
            "chunk_size": self.config.chunk_size,
            "chunk_overlap": self.config.chunk_overlap,
        }


processor = IngestionProcessor()