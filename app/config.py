from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Configuration
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.2

    # Database
    DATABASE_URL: str
    REDIS_URL: str

    # Vector Database
    QDRANT_URL: str
    QDRANT_COLLECTION: str = "kodee_knowledge"

    # Monitoring
    SENTRY_DSN: str = ""

    # App Settings
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_RPS: int = 10


settings = Settings()
