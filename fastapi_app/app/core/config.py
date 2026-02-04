from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    VLLM_IP_PORT: str
    VLLM_API_KEY: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()