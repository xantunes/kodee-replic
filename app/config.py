from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Configuration
    # OpenAI (direct), Azure OpenAI, or Kimi (Moonshot)
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = ""  # e.g. https://api.moonshot.ai/v1
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.2

    # FortiGate MCP — Multi-firewall support
    FORTIOS_INTERNET_HOST: str = ""
    FORTIOS_INTERNET_API_TOKEN: str = ""
    FORTIOS_INTERNET_VERIFY_SSL: bool = True
    FORTIOS_INTERNET_READONLY: bool = True

    FORTIOS_DATACENTER_HOST: str = ""
    FORTIOS_DATACENTER_API_TOKEN: str = ""
    FORTIOS_DATACENTER_VERIFY_SSL: bool = True
    FORTIOS_DATACENTER_READONLY: bool = True

    FORTIOS_VPN_HOST: str = ""
    FORTIOS_VPN_API_TOKEN: str = ""
    FORTIOS_VPN_VERIFY_SSL: bool = True
    FORTIOS_VPN_READONLY: bool = True

    FORTIOS_INTERNA_HOST: str = ""
    FORTIOS_INTERNA_API_TOKEN: str = ""
    FORTIOS_INTERNA_VERIFY_SSL: bool = True
    FORTIOS_INTERNA_READONLY: bool = True

    # Azure OpenAI (takes precedence if AZURE_OPENAI_ENDPOINT is set)
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"
    AZURE_OPENAI_DEPLOYMENT: str = ""  # e.g. "gpt-4.1"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-3-small"

    # Per-agent model overrides (default = OPENAI_MODEL or AZURE_OPENAI_DEPLOYMENT)
    # Use "mini" agents for fast/cheap tasks, "full" for complex reasoning
    MODEL_ROUTER: str = ""       # default: mini (fast classification)
    MODEL_GENERAL: str = ""      # default: mini (chitchat)
    MODEL_DNS: str = ""          # default: full (DNS management)
    MODEL_BACKUP: str = ""       # default: full (backup and restore)
    MODEL_MONITORING: str = ""   # default: full (infrastructure monitoring)
    MODEL_HANDOFF: str = ""      # default: mini (human escalation detection)
    MODEL_FORTIGATE: str = ""    # default: full (firewall management)

    # Database
    DATABASE_URL: str
    REDIS_URL: str

    # Vector Database
    QDRANT_URL: str
    QDRANT_COLLECTION: str = "kodee_knowledge"

    # Monitoring
    SENTRY_DSN: str = ""
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""

    # App Settings
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_RPS: int = 10


settings = Settings()
