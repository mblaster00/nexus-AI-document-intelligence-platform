import redis.asyncio as aioredis
import structlog

from app.core.config import settings

logger = structlog.get_logger()

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def publish_document(redis, document_id: str, file_path: str, mime_type: str) -> str:
    message = {
        "document_id": document_id,
        "file_path": file_path,
        "mime_type": mime_type,
    }

    stream_id = await redis.xadd(settings.redis_stream_name, message)

    logger.info(
        "document_published",
        document_id=document_id,
        stream_id=stream_id,
    )

    return stream_id