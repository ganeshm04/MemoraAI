"""
MemoraAI - Ingestion Processor
Unified ingestion pipeline for PDF, URL, and text sources.
"""

from typing import Optional, Literal
from dataclasses import dataclass, field
import structlog

from app.ingestion.pdf_parser import pdf_parser
from app.ingestion.url_scraper import url_scraper
from app.ingestion.text_cleaner import text_cleaner, content_filter
from app.ingestion.chunker import chunker, Chunker, ChunkMetadata

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
            
            chunks = self.chunker.chunk_text(
                text=text,
                document_id=0,
                source=file_path,
                custom_config={"file_path": file_path, **(metadata or {})},
            )
            
            return IngestionResult(
                success=True,
                source=file_path,
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
            
            chunks = self.chunker.chunk_text(
                text=text,
                document_id=0,
                source=url,
                custom_config={"url": url, **url_metadata, **(metadata or {})},
            )
            
            return IngestionResult(
                success=True,
                source=url,
                source_type="url",
                chunks_created=len(chunks),
                text_length=len(text),
                metadata={
                    "url": url,
                    **url_metadata,
                    **(metadata or {}),
                },
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
            
            return IngestionResult(
                success=True,
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