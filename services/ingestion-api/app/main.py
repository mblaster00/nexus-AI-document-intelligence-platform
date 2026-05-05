import structlog
import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.core.database import create_tables
from app.core.telemetry import setup_telemetry
from app.routes import documents, health

logger = structlog.get_logger()


def create_app() -> FastAPI:
    setup_telemetry(service_name="ingestion-api")
    logger.info("telemetry_setup", otel_enabled=settings.otel_enabled)
    app = FastAPI(
        title="Nexus Ingestion API",
        description="Document intake endpoint for the Nexus platform",
        version="0.1.0",
    )

    app.include_router(health.router, tags=["health"])
    app.include_router(documents.router, prefix="/documents", tags=["documents"])

    @app.on_event("startup")
    async def on_startup() -> None:
        await create_tables()
        logger.info("ingestion_api_started", port=settings.port)

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )