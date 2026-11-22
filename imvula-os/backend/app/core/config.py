from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All settings live here. Values come from the .env file."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Imvula OS"

    # ── Environment ──
    # "development" or "production"
    # In production, the app refuses to start with an unsafe JWT secret.
    environment: str = "development"

    # ── Database ──
    database_url: str = "sqlite:///./imvula_dev.db"

    # ── Auth ──
    jwt_secret: str = "dev-only-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    # ── CORS ──
    # Comma-separated list of allowed frontend origins.
    # Example: "https://app.imvulalabs.co.za,http://localhost:8080"
    allowed_origins: str = (
        "http://localhost:8080,"
        "http://127.0.0.1:8080,"
        "http://localhost:8000,"
        "http://localhost:8501,"
        "https://zithaewarty-11.github.io"
    )

    # ── AI Gateway ──
    ai_provider: str = "mock"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"

    @model_validator(mode="after")
    def _check_production_safety(self):
        if self.environment == "production":
            if "dev" in self.jwt_secret.lower():
                raise ValueError(
                    "Refusing to start: JWT_SECRET contains 'dev'. "
                    "Set a strong random JWT_SECRET in production."
                )
            if len(self.jwt_secret) < 32:
                raise ValueError(
                    "Refusing to start: JWT_SECRET must be at least 32 characters."
                )
            if self.database_url.startswith("sqlite"):
                raise ValueError(
                    "Refusing to start: production requires PostgreSQL, not SQLite. "
                    "Set DATABASE_URL to a postgresql:// URL."
                )
        return self

    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
