from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://nexus:nexus@localhost:5432/nexus"

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_stream_name: str = "nexus:documents"
    redis_consumer_group: str = "processing-workers"
    redis_consumer_name: str = "worker-1"
    redis_block_ms: int = 5000

    # Qdrant
    qdrant_url: str = "http://localhost:6333"

    # OpenAI
    openai_api_key: str = ""

    # OpenTelemetry
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_enabled: bool = True


settings = Settings()