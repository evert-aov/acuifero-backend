from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict


# ── Input ──────────────────────────────────────────────────────────────────────

class AlertaCreate(BaseModel):
    municipio_id:     int
    municipio_nombre: str
    tipo:             Literal["sequia", "sobreextraccion", "contaminacion"]
    descripcion:      str
    severidad:        Literal["warning", "critical"]


# ── Output ─────────────────────────────────────────────────────────────────────

class AlertaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:               int
    municipio_id:     int
    municipio_nombre: str
    tipo:             str
    descripcion:      str
    severidad:        str
    activa:           bool
    created_at:       Optional[datetime]
