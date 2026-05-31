from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    frontend_url: str = "http://localhost:4200"

    # Vertex AI (service account)
    google_application_credentials_vertex: Optional[str] = None
    vertex_project_id: Optional[str] = None
    vertex_location: str = "us-central1"
    vertex_model_name: str = "gemini-2.5-flash"

    # Gemini API Key (fallback)
    gemini_api_key: Optional[str] = None

    # Scheduler — intervalo entre lecturas simuladas (minutos)
    sensor_interval_minutes: int = 10

    class Config:
        env_file = ".env"

settings = Settings()
