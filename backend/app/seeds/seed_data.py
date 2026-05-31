"""
Poblar la base de datos con datos iniciales.
Ejecutar con:  python -m app.seeds.seed_data
"""
from app.database import SessionLocal, engine, Base
from app.models.municipio_model import Municipio
from app.models.alerta_model import Alerta

Base.metadata.create_all(bind=engine)

# score_riesgo y nivel_riesgo se calculan automáticamente desde los sensores.
# Ejecutar después del seed: POST /sensores/sync-all
# o: python -m app.seeds.seed_data  (llama a sync_all_scores automáticamente si hay sensores)
_MUNICIPIOS = [
    {"id": 1,  "nombre": "Santa Cruz de la Sierra", "lat": -17.7833, "lng": -63.1821, "region": "metropolitana",   "poblacion": 1453549},
    {"id": 2,  "nombre": "Charagua",                "lat": -19.7833, "lng": -63.2167, "region": "chaco",           "poblacion": 31823  },
    {"id": 3,  "nombre": "Cabezas",                 "lat": -18.7667, "lng": -63.3833, "region": "chaco",           "poblacion": 28450  },
    {"id": 4,  "nombre": "San Ignacio de Velasco",  "lat": -16.3667, "lng": -60.9500, "region": "chiquitania",     "poblacion": 52300  },
    {"id": 5,  "nombre": "Concepción",              "lat": -16.1333, "lng": -62.0167, "region": "chiquitania",     "poblacion": 39800  },
    {"id": 6,  "nombre": "San José de Chiquitos",   "lat": -17.8333, "lng": -60.7500, "region": "chiquitania",     "poblacion": 47200  },
    {"id": 7,  "nombre": "Montero",                 "lat": -17.3333, "lng": -63.2500, "region": "norte_integrado", "poblacion": 109800 },
    {"id": 8,  "nombre": "Warnes",                  "lat": -17.5000, "lng": -63.1667, "region": "norte_integrado", "poblacion": 91200  },
    {"id": 9,  "nombre": "Mineros",                 "lat": -17.1167, "lng": -63.0833, "region": "norte_integrado", "poblacion": 79300  },
    {"id": 10, "nombre": "Camiri",                  "lat": -20.0333, "lng": -63.5167, "region": "chaco",           "poblacion": 43200  },
    {"id": 11, "nombre": "Portachuelo",             "lat": -17.3500, "lng": -63.3833, "region": "norte_integrado", "poblacion": 45600  },
    {"id": 12, "nombre": "San Ramón",               "lat": -16.5667, "lng": -62.5333, "region": "chiquitania",     "poblacion": 18900  },
    {"id": 13, "nombre": "Vallegrande",             "lat": -18.4833, "lng": -64.1000, "region": "vallegrande",     "poblacion": 32100  },
    {"id": 14, "nombre": "Samaipata",               "lat": -18.1833, "lng": -63.8667, "region": "vallegrande",     "poblacion": 14200  },
    {"id": 15, "nombre": "Puerto Suárez",           "lat": -18.9500, "lng": -57.8000, "region": "pantanal",        "poblacion": 24700  },
]

_ALERTAS = [
    {"municipio_id": 2,  "municipio_nombre": "Charagua",               "tipo": "sequia",          "descripcion": "Reservorios al 8% de capacidad. Emergencia hídrica declarada. Riesgo de colapso del suministro en 45 días.",                "severidad": "critical"},
    {"municipio_id": 3,  "municipio_nombre": "Cabezas",                "tipo": "sequia",          "descripcion": "Nivel freático descendió 12m en los últimos 6 meses. Pozos comunales en riesgo de secarse.",                             "severidad": "critical"},
    {"municipio_id": 10, "municipio_nombre": "Camiri",                 "tipo": "sobreextraccion", "descripcion": "Extracción industrial supera la recarga natural del acuífero en 340%. Alerta de sobreexplotación.",                       "severidad": "critical"},
    {"municipio_id": 4,  "municipio_nombre": "San Ignacio de Velasco", "tipo": "sequia",          "descripcion": "Precipitaciones 65% por debajo del promedio histórico. Acuífero en estrés severo.",                                      "severidad": "warning"},
    {"municipio_id": 6,  "municipio_nombre": "San José de Chiquitos",  "tipo": "contaminacion",   "descripcion": "Detección de nitratos por encima del límite OMS. Posible filtración agroindustrial.",                                    "severidad": "warning"},
    {"municipio_id": 1,  "municipio_nombre": "Santa Cruz de la Sierra","tipo": "sobreextraccion", "descripcion": "Zonas de recarga en Lomas de Arena bajo presión urbanística. Monitoreo preventivo activo.",                             "severidad": "warning"},
]


def seed() -> None:
    db = SessionLocal()
    try:
        db.query(Alerta).delete()
        db.query(Municipio).delete()
        db.commit()

        for m in _MUNICIPIOS:
            db.add(Municipio(**m))
        db.commit()

        for a in _ALERTAS:
            db.add(Alerta(**a))
        db.commit()

        print("✅ Seed completado: 15 municipios, 6 alertas")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
