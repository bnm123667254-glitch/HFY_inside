"""
Configuration Management Module
Handles all application settings and environment variables
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # LLM Configuration
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    openai_api_base: str = Field("https://api.openai.com/v1", alias="OPENAI_API_BASE")
    openai_model: str = Field("gpt-4-turbo-preview", alias="OPENAI_MODEL")

    dashscope_api_key: Optional[str] = Field(None, alias="DASHSCOPE_API_KEY")
    qwen_model: str = Field("qwen2-72b-instruct", alias="QWEN_MODEL")

    llm_provider: str = Field("qwen", alias="LLM_PROVIDER")

    # Milvus Configuration
    milvus_host: str = Field("localhost", alias="MILVUS_HOST")
    milvus_port: int = Field(19530, alias="MILVUS_PORT")
    milvus_user: Optional[str] = Field(None, alias="MILVUS_USER")
    milvus_password: Optional[str] = Field(None, alias="MILVUS_PASSWORD")
    milvus_collection_name: str = Field("compliance_documents", alias="MILVUS_COLLECTION_NAME")

    # Embedding Configuration
    embedding_model: str = Field(
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        alias="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(768, alias="EMBEDDING_DIMENSION")

    # Application Configuration
    app_host: str = Field("0.0.0.0", alias="APP_HOST")
    app_port: int = Field(8000, alias="APP_PORT")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    enable_cors: bool = Field(True, alias="ENABLE_CORS")

    # Agent Configuration
    max_iterations: int = Field(10, alias="MAX_ITERATIONS")
    agent_timeout: int = Field(120, alias="AGENT_TIMEOUT")
    enable_memory: bool = Field(True, alias="ENABLE_MEMORY")
    memory_max_tokens: int = Field(2000, alias="MEMORY_MAX_TOKENS")

    # RAG Configuration
    top_k_documents: int = Field(5, alias="TOP_K_DOCUMENTS")
    similarity_threshold: float = Field(0.7, alias="SIMILARITY_THRESHOLD")
    chunk_size: int = Field(512, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(50, alias="CHUNK_OVERLAP")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()
