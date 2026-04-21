"""
Better Prompt — central configuration.
Values are loaded from the .env file automatically.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── API Keys ──────────────────────────────────────────────────────────
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    groq_api_key: str = ""

    # ── App ───────────────────────────────────────────────────────────────
    app_name: str = "Better Prompt"
    debug: bool = False

    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = "sqlite:///betterprompt.db"

    # ── Models ────────────────────────────────────────────────────────────
    default_model: str = "groq/llama-3.3-70b-versatile"
    judge_model: str = "groq/llama-3.3-70b-versatile"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )


settings = Settings()
