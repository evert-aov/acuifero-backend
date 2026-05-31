from fastapi import HTTPException
from app.dtos.prediccion_dto import PrediccionResponse

# Datos simulados realistas — reemplazar con modelo ML cuando haya datos reales
_PREDICCIONES: dict[int, dict] = {
    1:  {"tendencia": "descendente_leve",     "meses_criticos": 18, "proyeccion": [45, 43, 41, 40, 38, 37], "precipitacion_historica": [120, 95, 88, 110, 72, 65]},
    2:  {"tendencia": "critica_inmediata",    "meses_criticos": 1,  "proyeccion": [8,  5,  3,  1,  0,  0],  "precipitacion_historica": [45,  30, 22, 18, 10,  8]},
    3:  {"tendencia": "critica_inmediata",    "meses_criticos": 2,  "proyeccion": [12, 9,  6,  3,  1,  0],  "precipitacion_historica": [50,  38, 30, 25, 15, 12]},
    4:  {"tendencia": "descendente_severo",   "meses_criticos": 4,  "proyeccion": [28, 24, 20, 16, 12,  8], "precipitacion_historica": [80,  65, 55, 48, 38, 32]},
    5:  {"tendencia": "descendente_severo",   "meses_criticos": 5,  "proyeccion": [32, 28, 24, 20, 16, 12], "precipitacion_historica": [85,  70, 60, 52, 42, 35]},
    6:  {"tendencia": "descendente_severo",   "meses_criticos": 4,  "proyeccion": [30, 25, 21, 17, 13,  9], "precipitacion_historica": [78,  63, 53, 46, 36, 30]},
    7:  {"tendencia": "estable_riesgo_medio", "meses_criticos": 12, "proyeccion": [52, 50, 48, 47, 45, 44], "precipitacion_historica": [110, 95, 90, 85, 80, 78]},
    8:  {"tendencia": "estable_riesgo_medio", "meses_criticos": 14, "proyeccion": [48, 47, 45, 44, 42, 41], "precipitacion_historica": [108, 93, 88, 83, 78, 75]},
    9:  {"tendencia": "estable",              "meses_criticos": 24, "proyeccion": [72, 71, 70, 69, 68, 67], "precipitacion_historica": [125, 110, 105, 100, 95, 92]},
    10: {"tendencia": "critica_inmediata",    "meses_criticos": 2,  "proyeccion": [15, 11,  7,  3,  0,  0], "precipitacion_historica": [40,  28, 20, 15,  8,  5]},
    11: {"tendencia": "estable",              "meses_criticos": 30, "proyeccion": [78, 77, 76, 75, 74, 73], "precipitacion_historica": [130, 115, 110, 105, 100, 98]},
    12: {"tendencia": "descendente_severo",   "meses_criticos": 3,  "proyeccion": [26, 22, 18, 14, 10,  6], "precipitacion_historica": [75,  60, 50, 43, 33, 27]},
    13: {"tendencia": "estable_riesgo_medio", "meses_criticos": 10, "proyeccion": [55, 53, 51, 49, 47, 45], "precipitacion_historica": [112, 97, 92, 87, 82, 79]},
    14: {"tendencia": "estable",              "meses_criticos": 36, "proyeccion": [69, 68, 67, 66, 65, 64], "precipitacion_historica": [122, 107, 102, 97, 92, 89]},
    15: {"tendencia": "estable",              "meses_criticos": 48, "proyeccion": [85, 84, 83, 82, 81, 80], "precipitacion_historica": [140, 125, 120, 115, 110, 108]},
}


class PrediccionService:
    def get_by_municipio(self, municipio_id: int) -> PrediccionResponse:
        data = _PREDICCIONES.get(municipio_id)
        if not data:
            raise HTTPException(status_code=404, detail="Predicción no encontrada para este municipio")
        return PrediccionResponse(**data)
