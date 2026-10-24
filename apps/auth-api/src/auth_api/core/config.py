

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file=".env", extra="ignore")
    ENTRA_SECRET: str
    ENTRA_CLIENT_ID: str
    ENTRA_AUTHORITY:str
    ENTRA_REDIRECT_URL:str

settings = Settings()