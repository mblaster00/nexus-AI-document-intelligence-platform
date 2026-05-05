import asyncio

import structlog
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
import redis.asyncio as aioredis

from app.config import settings
from app.database import mark_completed, mark_failed, mark_processing
from ai.rag.chunking import split_text
from ai.rag.embeddings import embed_chunks
from ai.rag.pdf_parser import parse_pdf
from ai.rag.retrieval import ensure_collection, store_embeddings
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc import OTLPSpanExporter

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)

def setup_telemetry() -> None:
    if not settings.otel_enabled:
        return
    resource = Resource.create({"service.name": "processing-worker"})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

async def process_document(
    document_id: str,
    file_path: str,
    openai_client: AsyncOpenAI,
    qdrant_client: AsyncQdrantClient,
) -> None:
    await mark_processing(document_id)

    with tracer.start_as_current_span("process_document") as span:
        span.set_attribute("document.id", document_id)

        with tracer.start_as_current_span("parse_pdf"):
            parsed = parse_pdf(file_path=file_path, document_id=document_id)
            span.set_attribute("document.pages", parsed.total_pages)

        with tracer.start_as_current_span("chunk_text"):
            chunks = split_text(text=parsed.full_text, document_id=document_id)
            span.set_attribute("document.chunks", len(chunks))

        with tracer.start_as_current_span("embed_chunks") as embed_span:
            embedded = await embed_chunks(chunks=chunks, client=openai_client)
            embed_span.set_attribute("embedding.chunk_count", len(embedded))

        with tracer.start_as_current_span("store_embeddings"):
            await store_embeddings(client=qdrant_client, embedded_chunks=embedded)

    await mark_completed(document_id)


async def run_worker() -> None:
    setup_telemetry()
    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    qdrant_client = AsyncQdrantClient(url=settings.qdrant_url)

    await ensure_collection(qdrant_client)

    # Create consumer group if it does not exist
    try:
        await redis.xgroup_create(
            settings.redis_stream_name,
            settings.redis_consumer_group,
            id="0",
            mkstream=True,
        )
        logger.info("consumer_group_created", group=settings.redis_consumer_group)
    except Exception:
        # Group already exists
        pass

    logger.info("worker_started", consumer=settings.redis_consumer_name)

    while True:
        messages = await redis.xreadgroup(
            groupname=settings.redis_consumer_group,
            consumername=settings.redis_consumer_name,
            streams={settings.redis_stream_name: ">"},
            count=1,
            block=settings.redis_block_ms,
        )

        if not messages:
            continue

        for stream_name, stream_messages in messages:
            for message_id, data in stream_messages:
                document_id = data["document_id"]
                file_path = data["file_path"]

                logger.info(
                    "message_received",
                    document_id=document_id,
                    message_id=message_id,
                )

                try:
                    await process_document(
                        document_id=document_id,
                        file_path=file_path,
                        openai_client=openai_client,
                        qdrant_client=qdrant_client,
                    )
                    await redis.xack(
                        settings.redis_stream_name,
                        settings.redis_consumer_group,
                        message_id,
                    )
                    logger.info("message_acknowledged", message_id=message_id)

                except Exception as e:
                    logger.error(
                        "processing_failed",
                        document_id=document_id,
                        error=str(e),
                    )
                    await mark_failed(document_id=document_id, error=str(e))
                    await redis.xack(
                        settings.redis_stream_name,
                        settings.redis_consumer_group,
                        message_id,
                    )


if __name__ == "__main__":
    asyncio.run(run_worker())