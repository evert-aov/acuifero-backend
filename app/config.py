from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    gemini_api_key: str
    frontend_url: str = "http://localhost:4200"

    class Config:
        env_file = ".env"

settings = Settings()
