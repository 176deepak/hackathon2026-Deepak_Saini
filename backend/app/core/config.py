import os
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ENV(BaseSettings):
    ENVIRONMENT: str = Field("local", alias="ENVIRONMENT")

    APP_VERSION: str = Field(..., alias="APP_VERSION")
    APP_HOST: str = Field(..., alias="APP_HOST")
    APP_PORT: int = Field(..., alias="APP_PORT")
    APP_SECRET_KEY: str = Field(..., alias="APP_SECRET_KEY")
    APP_LOG_LEVEL: str = Field(..., alias="APP_LOG_LEVEL")
    APP_LOG_COLOR: bool = Field(True, alias="APP_LOG_COLOR")
    APP_LOGS_DIR: str = Field(..., alias="APP_LOGS_DIR")
    APP_JWT_ALGORITHM: str = Field(..., alias="APP_JWT_ALGORITHM")
    APP_JWT_SECRET_KEY: str = Field(..., alias="APP_JWT_SECRET_KEY")
    APP_JWT_EXP_TIME:int = Field(..., alias="APP_JWT_EXP_TIME")
    APP_BASE_URL: str = Field(..., alias="APP_BASE_URL")
    APP_DOCS_USERNAME: str = Field(..., alias="APP_DOCS_USERNAME")
    APP_DOCS_PASSWORD: str = Field(..., alias="APP_DOCS_PASSWORD")
    APP_SUPPORT_EMAIL: str = Field(..., alias="APP_SUPPORT_EMAIL")
    APP_SCHEDULER_MAX_INSTANCE: int = Field(..., alias="APP_SCHEDULER_MAX_INSTANCE")
    APP_APIS_VERSION: int = Field(..., alias="APP_APIS_VERSION")
    
    PG_DB_HOST: str = Field(..., alias="PG_DB_HOST")
    PG_DB_PORT: int = Field(..., alias="PG_DB_PORT")
    PG_DB_USER: str = Field(..., alias="PG_DB_USER")
    PG_DB_PASSWORD: str = Field(..., alias="PG_DB_PASSWORD")
    PG_DB_NAME: str = Field(..., alias="PG_DB_NAME")
    PG_MIN_CONNECTION: int = Field(..., alias="PG_MIN_CONNECTION")
    PG_MAX_CONNECTION: int = Field(..., alias="PG_MAX_CONNECTION")
    PG_DEFAULT_PAGE: int = Field(..., alias="PG_DEFAULT_PAGE")
    PG_DEFAULT_PAGINATION: int = Field(..., alias="PG_DEFAULT_PAGINATION")
    PG_DEFAULT_MAX_LIMIT: int = Field(..., alias="PG_DEFAULT_MAX_LIMIT")
    
    REDIS_HOST: str = Field(..., alias="REDIS_HOST")
    REDIS_PORT: int = Field(..., alias="REDIS_PORT")
    REDIS_USERNAME: str = Field(..., alias="REDIS_USERNAME")
    REDIS_PASSWORD: str = Field(..., alias="REDIS_PASSWORD")
    REDIS_DB: int = Field(..., alias="REDIS_DB")

    # LLM provider keys (leave blank if unused in your run mode)
    GOOGLE_API_KEY: str = Field("", alias="GOOGLE_API_KEY")
    OPENAI_API_KEY: str = Field("", alias="OPENAI_API_KEY")
    GROQ_API_KEY: str = Field("", alias="GROQ_API_KEY")

    # Knowledge base / vector index settings (defaults allow local-first runs)
    WHICH_KNOWLEDGE_BASE: str = Field("local", alias="WHICH_KNOWLEDGE_BASE")
    VECTOR_DB_NAME: str = Field("shopwave_kb", alias="VECTOR_DB_NAME")
    CHUNK_SIZE: int = Field(800, alias="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(120, alias="CHUNK_OVERLAP")
    KNOWLEDGE_BASE_GDRIVE_FILE_ID: str = Field("", alias="KNOWLEDGE_BASE_GDRIVE_FILE_ID")
    EMBEDDING_MODEL: str = Field("models/embedding-001", alias="EMBEDDING_MODEL")
    NO_TOP_K_CHUNKS: int = Field(8, alias="NO_TOP_K_CHUNKS")
    NO_TOP_N_CHUNKS: int = Field(4, alias="NO_TOP_N_CHUNKS")

    @computed_field
    @property
    def redis_uri(self) -> str:
        if self.ENVIRONMENT == "local" or envs.REDIS_HOST == "host.docker.internal":
            return (
                f"redis://{envs.REDIS_USERNAME}:{envs.REDIS_PASSWORD}"
                f"@{envs.REDIS_HOST}:{envs.REDIS_PORT}/{envs.REDIS_DB}"
            )

        return (
            f"rediss://{envs.REDIS_USERNAME}:{envs.REDIS_PASSWORD}"
            f"@{envs.REDIS_HOST}:{envs.REDIS_PORT}/{envs.REDIS_DB}"
        )

    @computed_field
    @property
    def cors_allowed_origins(self) -> str | list:
        if self.ENVIRONMENT == "prod":
            return []
        else:
            return "*"

    def __init__(self):
        super().__init__()
        os.makedirs(self.APP_LOGS_DIR, exist_ok=True)

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=False, 
        extra="ignore"
    )


envs = ENV()
