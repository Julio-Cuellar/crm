import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Aplicación
    ENVIRONMENT: str = "development"
    APP_PORT: int = 8000
    SECRET_KEY: str = "cambiame_por_una_llave_super_secreta_de_32_caracteres_minimo"

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://postgres:root@localhost:5432/crm"

    # MongoDB
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_DB: str = "jchat"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    # JWT
    JWT_SECRET: str = "supersecretkey"
    JWT_ACCESS_EXPIRE_MINUTES: float = 60.0
    JWT_REFRESH_EXPIRE_DAYS: int = 30

    # n8n
    N8N_BASE_URL: str = "http://localhost:5678"
    N8N_API_KEY: str = ""
    N8N_INBOUND_WEBHOOK_PATH: str = "/webhook/consultorio-inbound"
    N8N_CALLBACK_SECRET: str = ""
    N8N_BOT_STUB: bool = False

    # Bot / memoria conversacional resumida
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    # URL base para llamadas HTTP entre módulos dentro del mismo proceso
    # (ej. el fallback de scheduling cuando la proyección local de customer/service
    # todavía no fue actualizada por el evento correspondiente).
    INTERNAL_API_BASE_URL: str = "http://127.0.0.1:8000/api/v1"
    BOT_ENABLED_DEFAULT: bool = True
    BOT_SUMMARY_REFRESH_EVERY_TURNS: int = 6
    BOT_RECENT_TURNS: int = 2

    # Meta / WhatsApp
    META_GRAPH_API_BASE_URL: str = "https://graph.facebook.com"
    META_GRAPH_API_VERSION: str = "v25.0"
    META_WEBHOOK_VERIFY_TOKEN: str = "dev_verify_token_meta_crm"
    META_APP_SECRET: str = ""

    # Invitaciones
    INVITATION_EXPIRE_HOURS: int = 48

    # Configuración de carga del archivo .env
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
