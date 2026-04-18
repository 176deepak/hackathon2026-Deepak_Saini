import os
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ENV(BaseSettings):
    ENVIRONMENT: str = Field("local", alias="ENVIRONMENT")

    APP_NAME: str = Field("Resolvr", alias="APP_NAME")
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

    # Frontend/dashboard auth. Defaults to docs credentials if left blank.
    APP_AUTH_USERNAME: str = Field("", alias="APP_AUTH_USERNAME")
    APP_AUTH_PASSWORD: str = Field("", alias="APP_AUTH_PASSWORD")
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

    HISTORY_TTL: int = Field(60 * 60, alias="HISTORY_TTL")
    HISTORY_TTL_REFRESH_ON_READ: bool = Field(True, alias="HISTORY_TTL_REFRESH_ON_READ")

    AGENT_AUTORUN: bool = Field(False, alias="AGENT_AUTORUN")
    AGENT_POLL_SECONDS: int = Field(30, alias="AGENT_POLL_SECONDS")
    AGENT_MAX_CONCURRENCY: int = Field(8, alias="AGENT_MAX_CONCURRENCY")
    AGENT_MAX_TICKETS_PER_TICK: int = Field(20, alias="AGENT_MAX_TICKETS_PER_TICK")
    AGENT_MAX_RETRIES: int = Field(2, alias="AGENT_MAX_RETRIES")
    AGENT_FAULT_INJECTION: bool = Field(True, alias="AGENT_FAULT_INJECTION")
    AGENT_DRAW_GRAPH: bool = Field(False, alias="AGENT_DRAW_GRAPH")

    GOOGLE_API_KEY: str = Field("", alias="GOOGLE_API_KEY")
    OPENAI_API_KEY: str = Field("", alias="OPENAI_API_KEY")
    GROQ_API_KEY: str = Field("", alias="GROQ_API_KEY")

    WHICH_KNOWLEDGE_BASE: str = Field("local", alias="WHICH_KNOWLEDGE_BASE")
    VECTOR_DB_NAME: str = Field("shopwave_kb", alias="VECTOR_DB_NAME")
    CHUNK_SIZE: int = Field(800, alias="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(120, alias="CHUNK_OVERLAP")
    KNOWLEDGE_BASE_GDRIVE_FILE_ID: str=Field("", alias="KNOWLEDGE_BASE_GDRIVE_FILE_ID")
    EMBEDDING_MODEL: str = Field("models/embedding-001", alias="EMBEDDING_MODEL")
    NO_TOP_K_CHUNKS: int = Field(8, alias="NO_TOP_K_CHUNKS")
    NO_TOP_N_CHUNKS: int = Field(4, alias="NO_TOP_N_CHUNKS")

    @computed_field
    @property
    def redis_uri(self) -> str:
        if self.ENVIRONMENT == "local" or self.REDIS_HOST == "host.docker.internal":
            return (
                f"redis://{self.REDIS_USERNAME}:{self.REDIS_PASSWORD}"
                f"@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            )

        return (
            f"rediss://{self.REDIS_USERNAME}:{self.REDIS_PASSWORD}"
            f"@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
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
