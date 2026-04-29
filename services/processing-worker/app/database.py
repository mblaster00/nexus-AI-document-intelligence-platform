from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import structlog

from app.config import settings

logger = structlog.get_logger()

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def mark_processing(document_id: str) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("""
                UPDATE documents
                SET status = 'processing', updated_at = now()
                WHERE id = :id
            """),
            {"id": document_id},
        )
        await session.commit()
        logger.info("document_status_updated", document_id=document_id, status="processing")


async def mark_completed(document_id: str) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("""
                UPDATE documents
                SET status = 'completed', updated_at = now()
                WHERE id = :id
            """),
            {"id": document_id},
        )
        await session.commit()
        logger.info("document_status_updated", document_id=document_id, status="completed")


async def mark_failed(document_id: str, error: str) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("""
                UPDATE documents
                SET status = 'failed', error_message = :error, updated_at = now()
                WHERE id = :id
            """),
            {"id": document_id, "error": error},
        )
        await session.commit()
        logger.info("document_status_updated", document_id=document_id, status="failed", error=error)