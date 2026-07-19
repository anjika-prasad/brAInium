"""
Central configuration. All external service endpoints, model names and
credentials are pulled from environment variables so the same codebase
runs unchanged across a laptop demo, a Docker-Compose stack, or a cloud
deployment.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    llama_base_url: str = "http://localhost:11434"
    llama_model: str = "llama3.1"

    # Embeddings
    embedding_model: str = "BAAI/bge-large-en-v1.5"
    embedding_dim: int = 1024

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "ikb_chunks"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "changeme123"

    # Postgres
    postgres_dsn: str = "postgresql+asyncpg://ikb:ikb@localhost:5432/ikb"

    # Storage
    storage_backend: str = "local"
    local_storage_dir: str = "./storage"
    s3_bucket: str = ""
    s3_region: str = ""

    # App
    app_env: str = "dev"
    max_upload_mb: int = 50


@lru_cache
def get_settings() -> Settings:
    return Settings()
