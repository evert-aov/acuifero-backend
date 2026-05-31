from datetime import datetime
from pydantic import BaseModel


class ReadingResponse(BaseModel):
    timestamp:         datetime
    municipio_id:      int
    nivel_freatico_m:  float
    humedad_suelo_pct: float
    extraccion_lps:    float
    precipitacion_mm:  float

    model_config = {"from_attributes": True}
