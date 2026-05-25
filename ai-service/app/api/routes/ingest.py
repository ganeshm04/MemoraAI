"""
MemoraAI - API Routes: Ingestion
Document ingestion endpoints for PDF, URL, and text.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional
import structlog

from app.ingestion.processor import processor, IngestionProcessor, IngestionConfig
from app.security.validator import validator, chunking_validator

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingestion"])


class PDFIngestionRequest(BaseModel):
    file_path: str = Field(..., description="Path to PDF file")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")
    chunk_size: Optional[int] = Field(default=700, description="Chunk size in tokens")
    chunk_overlap: Optional[int] = Field(default=100, description="Chunk overlap in tokens")


class URLIngestionRequest(BaseModel):
    url: str = Field(..., description="URL to scrape")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")
    chunk_size: Optional[int] = Field(default=700)
    chunk_overlap: Optional[int] = Field(default=100)


class TextIngestionRequest(BaseModel):
    text: str = Field(..., description="Text content to ingest")
    source: str = Field(..., description="Source identifier")
    metadata: Optional[dict] = Field(default=None)
    chunk_size: Optional[int] = Field(default=700)
    chunk_overlap: Optional[int] = Field(default=100)


class IngestionResponse(BaseModel):
    success: bool
    source: str
    source_type: str
    chunks_created: int
    text_length: int
    errors: list[str]


@router.post("/pdf", response_model=IngestionResponse)
async def ingest_pdf(request: PDFIngestionRequest):
    """Ingest PDF document."""
    logger.info("pdf_ingestion_request", file_path=request.file_path)

    validation = chunking_validator.validate_config(
        request.chunk_size or 700,
        request.chunk_overlap or 100,
    )
    if not validation.valid:
        raise HTTPException(status_code=400, detail=validation.errors)

    try:
        result = await processor.ingest_pdf(
            file_path=request.file_path,
            metadata=request.metadata,
        )
        return IngestionResponse(
            success=result.success,
            source=result.source,
            source_type=result.source_type,
            chunks_created=result.chunks_created,
            text_length=result.text_length,
            errors=result.errors,
        )
    except Exception as e:
        logger.error("pdf_ingestion_api_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/url", response_model=IngestionResponse)
async def ingest_url(request: URLIngestionRequest):
    """Ingest content from URL."""
    logger.info("url_ingestion_request", url=request.url)

    validation = validator.validate_url(request.url)
    if not validation.valid:
        raise HTTPException(status_code=400, detail=validation.errors)

    validation = chunking_validator.validate_config(
        request.chunk_size or 700,
        request.chunk_overlap or 100,
    )
    if not validation.valid:
        raise HTTPException(status_code=400, detail=validation.errors)

    try:
        result = await processor.ingest_url(
            url=request.url,
            metadata=request.metadata,
        )
        return IngestionResponse(
            success=result.success,
            source=result.source,
            source_type=result.source_type,
            chunks_created=result.chunks_created,
            text_length=result.text_length,
            errors=result.errors,
        )
    except Exception as e:
        logger.error("url_ingestion_api_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text", response_model=IngestionResponse)
async def ingest_text(request: TextIngestionRequest):
    """Ingest plain text content."""
    logger.info("text_ingestion_request", source=request.source, length=len(request.text))

    validation = validator.validate_text_input(request.text)
    if not validation.valid:
        raise HTTPException(status_code=400, detail=validation.errors)

    validation = chunking_validator.validate_config(
        request.chunk_size or 700,
        request.chunk_overlap or 100,
    )
    if not validation.valid:
        raise HTTPException(status_code=400, detail=validation.errors)

    try:
        result = await processor.ingest_text(
            text=request.text,
            source=request.source,
            metadata=request.metadata,
        )
        return IngestionResponse(
            success=result.success,
            source=result.source,
            source_type=result.source_type,
            chunks_created=result.chunks_created,
            text_length=result.text_length,
            errors=result.errors,
        )
    except Exception as e:
        logger.error("text_ingestion_api_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def ingest_batch(sources: list[dict]):
    """Ingest multiple sources in batch."""
    logger.info("batch_ingestion_request", total=len(sources))

    try:
        results = await processor.ingest_batch(sources)
        return {
            "total": len(sources),
            "successful": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "results": [
                {
                    "success": r.success,
                    "source": r.source,
                    "source_type": r.source_type,
                    "chunks_created": r.chunks_created,
                    "errors": r.errors,
                }
                for r in results
            ],
        }
    except Exception as e:
        logger.error("batch_ingestion_api_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))