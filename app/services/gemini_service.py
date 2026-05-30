import google.generativeai as genai
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.config import settings
from app.dtos.municipio_dto import MunicipioResponse
from app.dtos.prediccion_dto import PrediccionResponse, GeminiResumenResponse
from app.repositories.municipio_repository import MunicipioRepository
from app.services.prediccion_service import PrediccionService

genai.configure(api_key=settings.gemini_api_key)
_model = genai.GenerativeModel("gemini-1.5-flash")


class GeminiService:
    def __init__(self, db: Session):
        self.municipio_repo = MunicipioRepository(db)
        self.prediccion_svc = PrediccionService()

    def generar_resumen(self, municipio_id: int) -> GeminiResumenResponse:
        # 1. Obtener datos
        municipio_orm = self.municipio_repo.get_by_id(municipio_id)
        if not municipio_orm:
            raise HTTPException(status_code=404, detail="Municipio no encontrado")

        municipio = MunicipioResponse.model_validate(municipio_orm)
        prediccion = self.prediccion_svc.get_by_municipio(municipio_id)

        # 2. Construir prompt
        prompt = self._build_prompt(municipio, prediccion)

        # 3. Llamar a Gemini
        try:
            response = _model.generate_content(prompt)
            texto = response.text
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error al consultar Gemini: {str(e)}")

        return GeminiResumenResponse(municipio=municipio.nombre, resumen=texto)

    # ── helpers ────────────────────────────────────────────────────────────────

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
