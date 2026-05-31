from typing import Literal
from pydantic import BaseModel, ConfigDict


# ── Input ──────────────────────────────────────────────────────────────────────

class MunicipioCreate(BaseModel):
    nombre:       str
    lat:          float
    lng:          float
    region:       str
    poblacion:    int
    nivel_riesgo: Literal["bajo", "medio", "alto", "critico"] = "bajo"
    score_riesgo: float = 0.0


# ── Output ─────────────────────────────────────────────────────────────────────

class MunicipioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:           int
    nombre:       str
    lat:          float
    lng:          float
    region:       str
    poblacion:    int
    nivel_riesgo: str
    score_riesgo: float
