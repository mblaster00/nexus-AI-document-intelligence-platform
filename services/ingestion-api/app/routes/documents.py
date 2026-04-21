import uuid
from pathlib import Path

import aiofiles
import structlog
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.queue import publish_document
from app.models.document import Document, DocumentStatus

router = APIRouter()
logger = structlog.get_logger()


class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    mime_type: str
    file_size_bytes: int


class DocumentDetail(DocumentResponse):
    error_message: str | None
    created_at: str
    updated_at: str


@router.post(
    "/",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a document for processing",
)
async def upload_document(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    if file.content_type not in settings.allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}",
        )

    content = await file.read()
    size_bytes = len(content)
    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_size_mb}MB limit",
        )

    document_id = str(uuid.uuid4())
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    file_path = str(upload_path / f"{document_id}.pdf")

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    document = Document(
        id=document_id,
        filename=file.filename or "unnamed.pdf",
        mime_type=file.content_type or "application/pdf",
        file_path=file_path,
        file_size_bytes=size_bytes,
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    await publish_document(
        document_id=document_id,
        file_path=file_path,
        mime_type=file.content_type or "application/pdf",
    )

    logger.info(
        "document_accepted",
        document_id=document_id,
        filename=file.filename,
        size_bytes=size_bytes,
    )

    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        status=document.status,
        mime_type=document.mime_type,
        file_size_bytes=document.file_size_bytes,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetail,
    summary="Get document status",
)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentDetail:
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    return DocumentDetail(
        id=document.id,
        filename=document.filename,
        status=document.status,
        mime_type=document.mime_type,
        file_size_bytes=document.file_size_bytes,
        error_message=document.error_message,
        created_at=document.created_at.isoformat(),
        updated_at=document.updated_at.isoformat(),
    )