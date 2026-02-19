from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout: float = 120.0

    max_commits: int = 20
    max_diff_chars: int = 8000

    model_config = SettingsConfigDict(env_file=".env", env_prefix="FEEDY_")


settings = Settings()
