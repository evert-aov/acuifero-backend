from typing import List
from pydantic import BaseModel


# ── Predicción ─────────────────────────────────────────────────────────────────

class PrediccionResponse(BaseModel):
    tendencia:                str
    meses_criticos:           int
    proyeccion:               List[float]
    precipitacion_historica:  List[float]


# ── Gemini ─────────────────────────────────────────────────────────────────────

class GeminiResumenRequest(BaseModel):
    municipio_id: int


class GeminiResumenResponse(BaseModel):
    municipio: str
    resumen:   str
