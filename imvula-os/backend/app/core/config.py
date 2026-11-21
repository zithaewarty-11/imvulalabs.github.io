from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All settings live here. Values come from the .env file."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Imvula OS"
    database_url: str = "sqlite:///./imvula_dev.db"
    jwt_secret: str = "dev-only-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    # ── AI Gateway (Phase 5) ──
    # "mock"     — deterministic fake AI, no API key, zero cost (default, safe)
    # "deepseek" — real DeepSeek API, requires DEEPSEEK_API_KEY
    ai_provider: str = "mock"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"


settings = Settings()
