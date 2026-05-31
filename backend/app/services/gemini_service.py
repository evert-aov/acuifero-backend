import os
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.config import settings
from app.dtos.municipio_dto import MunicipioResponse
from app.dtos.prediccion_dto import PrediccionResponse, GeminiResumenResponse
from app.repositories.municipio_repository import MunicipioRepository
from app.services.prediccion_service import PrediccionService

_model = None


def _init_model():
    """
    Inicializa el modelo de IA con este orden de prioridad:
    1. Vertex AI con service account JSON
    2. Gemini API Key (fallback)
    """
    global _model

    # Intento 1: Vertex AI
    key_path = settings.google_application_credentials_vertex
    if key_path and os.path.exists(key_path) and settings.vertex_project_id:
        from google.auth import default
        from google.oauth2 import service_account
        import vertexai
        from vertexai.generative_models import GenerativeModel

        try:
            creds = service_account.Credentials.from_service_account_file(key_path)
        except Exception:
            creds, _ = default()

        vertexai.init(
            project=settings.vertex_project_id,
            location=settings.vertex_location,
            credentials=creds,
        )
        _model = GenerativeModel(settings.vertex_model_name)
        return

    # Intento 2: Gemini API Key (fallback)
    if settings.gemini_api_key:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        _model = genai.GenerativeModel("gemini-1.5-flash")
        return

    raise RuntimeError(
        "Sin credenciales de IA. Configura GOOGLE_APPLICATION_CREDENTIALS_VERTEX "
        "+ VERTEX_PROJECT_ID, o GEMINI_API_KEY como fallback."
    )


def _get_model():
    global _model
    if _model is None:
        _init_model()
    return _model


class GeminiService:
    def __init__(self, db: Session):
        self.municipio_repo = MunicipioRepository(db)
        self.prediccion_svc = PrediccionService(db)

    def generar_resumen(self, municipio_id: int) -> GeminiResumenResponse:
        municipio_orm = self.municipio_repo.get_by_id(municipio_id)
        if not municipio_orm:
            raise HTTPException(status_code=404, detail="Municipio no encontrado")

        municipio = MunicipioResponse.model_validate(municipio_orm)
        prediccion = self.prediccion_svc.get_by_municipio(municipio_id)

        prompt = self._build_prompt(municipio, prediccion)

        try:
            model = _get_model()
            response = model.generate_content(prompt)
            texto = response.text
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error al consultar Gemini: {str(e)}")

        return GeminiResumenResponse(municipio=municipio.nombre, resumen=texto)

    @staticmethod
    def _build_prompt(municipio: MunicipioResponse, prediccion: PrediccionResponse) -> str:
        return f"""
Eres un sistema experto en recursos hídricos del departamento de Santa Cruz, Bolivia.
Genera un análisis ejecutivo conciso (máximo 4 párrafos) para autoridades municipales y productores agrícolas.

Municipio: {municipio.nombre}
Región: {municipio.region}
Población: {municipio.poblacion:,} habitantes
Nivel de riesgo hídrico: {municipio.nivel_riesgo.upper()}
Score de riesgo: {municipio.score_riesgo * 100:.0f}/100
Tendencia: {prediccion.tendencia}
Meses hasta situación crítica (si no se actúa): {prediccion.meses_criticos}

Incluye:
1. Diagnóstico actual del acuífero
2. Impacto en agricultura y ganadería local
3. Acciones inmediatas recomendadas
4. Proyección a 6 meses

Responde en español. Sé específico con Santa Cruz. No uses markdown, solo texto plano.
""".strip()
