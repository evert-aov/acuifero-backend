from datetime import datetime
from pydantic import BaseModel


class SensorResponse(BaseModel):
    id:            int
    municipio_id:  int
    nombre:        str
    zona:          str
    lat:           float
    lng:           float
    activo:        bool

    model_config = {"from_attributes": True}


class SensorScoreResponse(BaseModel):
    sensor_id:         int
    nombre:            str
    zona:              str
    lat:               float
    lng:               float
    score:             float   # 0.0 – 1.0
    nivel_freatico_m:  float
    tendencia_m_dia:   float   # pendiente de los últimos 30 días (m/día)
    nivel_riesgo:      str     # bajo | medio | alto | critico
    timestamp:         datetime


class MunicipioSensorAggregation(BaseModel):
    municipio_id:   int
    score_agregado: float   # resultado del Max-Pooling
    nivel_riesgo:   str
    sensores:       list[SensorScoreResponse]
    sensor_critico: SensorScoreResponse | None  # el sensor de mayor riesgo
