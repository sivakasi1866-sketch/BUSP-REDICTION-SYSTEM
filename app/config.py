from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Partners Bus Prediction"
    API_V1_STR: str = "/api"

    # Override in Vercel dashboard with a strong random value:
    # python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = "partners-bus-secret-key-development-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Local dev: sqlite:///./partners_bus.db (default)
    # Vercel:    set DATABASE_URL env var in Vercel dashboard to Neon PostgreSQL URL
    DATABASE_URL: str = "sqlite:///./partners_bus.db"

    # ETA & Notification settings
    NOTIFICATION_THRESHOLDS: list[int] = [10, 5, 2, 0]

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",          # loads .env file in local dev
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
