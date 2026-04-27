from dataclasses import dataclass

import structlog
from openai import AsyncOpenAI

from ai.rag.chunking import Chunk

logger = structlog.get_logger()

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


@dataclass
class EmbeddedChunk:
    chunk: Chunk
    embedding: list[float]
    model: str


async def embed_chunks(
    chunks: list[Chunk],
    client: AsyncOpenAI,
) -> list[EmbeddedChunk]:
    if not chunks:
        return []

    texts = [chunk.text for chunk in chunks]

    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )

    logger.info(
        "chunks_embedded",
        document_id=chunks[0].document_id,
        chunk_count=len(chunks),
        model=EMBEDDING_MODEL,
        total_tokens=response.usage.total_tokens,
    )

    return [
        EmbeddedChunk(
            chunk=chunk,
            embedding=result.embedding,
            model=EMBEDDING_MODEL,
        )
        for chunk, result in zip(chunks, response.data)
    ]