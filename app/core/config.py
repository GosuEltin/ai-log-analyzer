from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    MODEL_NAME: str = "openai/gpt-oss-20b"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()