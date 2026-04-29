from dataclasses import dataclass
import uuid
import structlog
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from ai.rag.embeddings import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL

logger = structlog.get_logger()

COLLECTION_NAME = "documents"


@dataclass
class RetrievedChunk:
    document_id: str
    chunk_index: int
    text: str
    score: float
    page_number: int | None = None


async def ensure_collection(client: AsyncQdrantClient) -> None:
    collections = await client.get_collections()
    names = [c.name for c in collections.collections]

    if COLLECTION_NAME not in names:
        await client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSIONS,
                distance=Distance.COSINE,
            ),
        )
        logger.info("qdrant_collection_created", collection=COLLECTION_NAME)


async def store_embeddings(
    client: AsyncQdrantClient,
    embedded_chunks: list,
) -> None:
    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{ec.chunk.document_id}_{ec.chunk.index}")),
            vector=ec.embedding,
            payload={
                "document_id": ec.chunk.document_id,
                "chunk_index": ec.chunk.index,
                "page_number": ec.chunk.page_number,
                "text": ec.chunk.text,
            },
        )
        for ec in embedded_chunks
    ]

    await client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    logger.info(
        "embeddings_stored",
        document_id=embedded_chunks[0].chunk.document_id,
        chunk_count=len(points),
    )


async def search(
    client: AsyncQdrantClient,
    openai_client: AsyncOpenAI,
    query: str,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    response = await openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query],
    )
    query_vector = response.data[0].embedding

    results = await client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
    )

    logger.info(
        "qdrant_search",
        query=query[:50],
        top_k=top_k,
        results_count=len(results),
    )

    return [
        RetrievedChunk(
            document_id=r.payload["document_id"],
            chunk_index=r.payload["chunk_index"],
            text=r.payload["text"],
            score=r.score,
            page_number=r.payload.get("page_number"),
        )
        for r in results
    ]