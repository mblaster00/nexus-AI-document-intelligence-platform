from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    database_url: str = "postgresql+asyncpg://nexus:nexus@localhost:5432/nexus"
    redis_url: str = "redis://localhost:6379"
    redis_stream_name: str = "nexus:documents"

    upload_dir: str = "/tmp/nexus/uploads"
    max_upload_size_mb: int = 20
    allowed_mime_types: list[str] = ["application/pdf"]


settings = Settings()