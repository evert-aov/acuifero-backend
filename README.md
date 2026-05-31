# Acuífero-Data SCZ

**Hackathon Build With AI 2026 — Google Developer Groups | Equipo NINJE**

## Entregables

| Recurso | Enlace |
|---|---|
| Video demo (YouTube) | https://youtu.be/ybwgBlt1zCQ |
| Documento técnico (PDF) | [`docs/AcuiferoDataSCZ_DocumentoTecnico.pdf`](docs/AcuiferoDataSCZ_DocumentoTecnico.pdf) |
| Diapositivas (PDF) | [`docs/Acuifero-Data-SCZ-Presentacion.pdf`](docs/Acuifero-Data-SCZ-Presentacion.pdf) |
| Repositorio público | https://github.com/evert-aov/acuifero-backend |

---

## Información del Proyecto

Acuífero-Data SCZ es una plataforma de inteligencia hídrica para el monitoreo continuo y predicción anticipada del estrés hídrico en los acuíferos del departamento de Santa Cruz, Bolivia.

El sistema procesa datos de sensores distribuidos en tiempo real, aplica modelos de series temporales (EWMA + regresión lineal) para predecir el horizonte de crisis de cada municipio con meses de anticipación, e integra análisis ejecutivo con Gemini AI.

---

## Arquitectura general

```
Sensores físicos (3–5 / municipio)
        │  lecturas cada 10 min (APScheduler)
        ▼
  PostgreSQL — tabla readings (sensor_id, timestamp, nivel_freatico_m, …)
        │
        ├─ EWMA Composite Score por sensor
        ├─ Max-Pooling → score del municipio
        ├─ Min-Max Cross-Normalization → riesgo relativo
        └─ EWMA + Regresión lineal dual → predicción 6 meses
        │
  FastAPI REST API
        │
  Angular 21 SPA — mapa Leaflet, gráficos Chart.js, análisis Gemini
```

---

## Estructura del Proyecto

```
acuifero-data-backend/
├── backend/
│   ├── app/
│   │   ├── controllers/
│   │   │   ├── municipio_controller.py
│   │   │   ├── reading_controller.py
│   │   │   ├── sensor_controller.py       # scores, live, sync-all, scheduler status
│   │   │   ├── prediccion_controller.py   # predicción real desde sensores
│   │   │   ├── alerta_controller.py
│   │   │   └── gemini_controller.py
│   │   ├── models/
│   │   │   ├── municipio_model.py
│   │   │   ├── sensor_model.py            # tabla sensores (zona, offset_nivel, factor_extrac)
│   │   │   ├── reading_model.py           # +sensor_id FK
│   │   │   └── alerta_model.py
│   │   ├── services/
│   │   │   ├── sensor_service.py          # EWMA scoring + Max-Pooling + Min-Max
│   │   │   ├── prediccion_service.py      # EWMA + regresión lineal dual (365d/90d)
│   │   │   ├── scheduler_service.py       # APScheduler — tick cada N minutos
│   │   │   ├── municipio_service.py
│   │   │   ├── alerta_service.py
│   │   │   └── gemini_service.py
│   │   ├── repositories/
│   │   │   ├── sensor_repository.py
│   │   │   ├── municipio_repository.py
│   │   │   ├── reading_repository.py
│   │   │   └── alerta_repository.py
│   │   ├── dtos/
│   │   │   ├── sensor_dto.py              # SensorScoreResponse, MunicipioSensorAggregation
│   │   │   ├── prediccion_dto.py
│   │   │   ├── municipio_dto.py
│   │   │   ├── reading_dto.py
│   │   │   └── alerta_dto.py
│   │   ├── seeds/
│   │   │   ├── seed_data.py               # municipios + alertas (sin scores hardcodeados)
│   │   │   ├── seed_multi_sensor.py       # 51 sensores + 730 días de lecturas
│   │   │   └── seed_sensors.py            # seed original (1 lectura/municipio/día)
│   │   ├── config.py                      # +SENSOR_INTERVAL_MINUTES
│   │   ├── database.py
│   │   └── main.py                        # lifespan: scheduler + precompute trends
│   ├── .keys/                             # credenciales Vertex AI (no en git)
│   ├── .env                               # variables de entorno (no en git)
│   ├── Dockerfile
│   ├── cloudbuild.yaml
│   └── requirements.txt
│
├── frontend/
│   └── src/app/
│       ├── core/
│       │   ├── models/municipio.model.ts  # +SensorScore, MunicipioSensorAggregation
│       │   └── services/
│       │       ├── api.ts                 # +getSensorScores()
│       │       └── datos-locales.service.ts
│       ├── pages/
│       │   ├── dashboard/                 # mapa + KPIs + tabla (datos reales)
│       │   └── municipio-detalle/         # predicción + tabs histórico/proyección + sensores
│       └── shared/components/
│           ├── grafico-tendencia/         # +mode input, meses reales, umbral crítico
│           ├── mapa-scz/                  # Leaflet con ngOnDestroy + scrollWheelZoom:false
│           ├── gemini-panel/
│           ├── alerta-card/
│           ├── stat-card/
│           └── navbar/
│
├── docs/
│   └── sensores-multi-sensor.md          # algoritmo completo documentado
├── .gitignore
└── README.md
```

---

## Tecnologías

### Backend
| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.12 | |
| FastAPI | 0.111.0 | API REST + lifespan events |
| APScheduler | 3.10.4 | Monitoreo en tiempo real (tick cada N min) |
| SQLAlchemy | 2.0.30 | ORM + consultas |
| NumPy / Pandas | ≥1.26 / ≥2.2 | EWMA, regresión lineal, simulación |
| Pydantic | 2.7.1 | Schemas y validación |
| PostgreSQL | 18 | Base de datos principal |

### Frontend
| Tecnología | Versión | Uso |
|---|---|---|
| Angular | 21.2.x | SPA standalone components |
| Leaflet.js | — | Mapa interactivo de riesgo |
| Chart.js | — | Gráfico histórico y proyección |
| Tailwind CSS | 3.4.x | Estilos |

### Inteligencia Artificial
| Tecnología | Uso |
|---|---|
| Gemini 2.5 Flash (Vertex AI) | Análisis ejecutivo por municipio |
| EWMA + Regresión lineal | Predicción del horizonte de crisis |
| Max-Pooling ponderado | Agregación multi-sensor sin ocultar crisis |

---

## Instalación y Ejecución

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Crear `backend/.env`:

```env
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/acuifero_db
GOOGLE_APPLICATION_CREDENTIALS_VERTEX=/ruta/a/svc-key.json
VERTEX_PROJECT_ID=mi-proyecto-gcp
VERTEX_LOCATION=us-central1
VERTEX_MODEL_NAME=gemini-2.5-flash
SENSOR_INTERVAL_MINUTES=10
```

Iniciar el servidor:

```bash
uvicorn app.main:app --reload
```

Al arrancar, FastAPI ejecuta automáticamente:
- Precálculo de tendencias EWMA de los 51 sensores
- Primer tick del scheduler (lecturas iniciales)
- APScheduler activo cada `SENSOR_INTERVAL_MINUTES` minutos

API disponible en `http://localhost:8000` · Swagger en `http://localhost:8000/docs`

### 2. Poblar la base de datos (primera vez)

```bash
# Municipios y alertas base
python -m app.seeds.seed_data

# 51 sensores + 730 días de lecturas históricas (~37 k registros)
python -m app.seeds.seed_multi_sensor

# Calcular score_riesgo y nivel_riesgo desde datos reales
curl -X POST "http://localhost:8000/sensores/sync-all?days=730"
```

### 3. Frontend

```bash
cd frontend
npm install
npm run start
```

Disponible en `http://localhost:4200`

---

## Endpoints principales

### Sensores y Riesgo
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/sensores/{id}/scores?days=730` | Score EWMA por sensor + score agregado Max-Pooling |
| `GET` | `/sensores/{id}/live` | Lectura en tiempo real (tick bajo demanda) |
| `GET` | `/sensores/scheduler/status` | Estado del scheduler: último tick, lecturas generadas |
| `POST` | `/sensores/sync-all` | Recalcula scores de todos los municipios |

### Predicción
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/prediccion/{id}` | EWMA + regresión lineal dual → meses hasta crisis, proyección 6 meses, tendencia |

### Lecturas históricas
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/readings/{id}?days=90` | Últimas N lecturas del municipio (incluye lecturas del scheduler) |

---

## Módulo de Riesgo: algoritmos

### Score por sensor — EWMA Composite

```
score = 0.35 × agotamiento          (1 - EWMA_7d / pico_histórico)
      + 0.30 × cruce_EWMA           ((EWMA_90d - EWMA_7d) / σ, normalizado a 3σ)
      + 0.20 × velocidad_EWMA       (pendiente EWMA_90d últimos 30d)
      + 0.15 × presión_extracción   (EWMA_7d_extracción / max_extracción)
```

### Agregación por municipio — Max-Pooling

```
score_municipio = 0.7 × max(scores_sensores)
                + 0.3 × promedio_cuadrático(scores_sensores)
```

Un sensor en crisis domina el resultado. 4 sensores en 0.2 + 1 en 0.9 → score **0.87 crítico** (no 0.34 con AVG).

### Calibración relativa — Min-Max γ=0.5

```
score_final = ((raw - min_global) / (max_global - min_global)) ^ 0.5
```

Score 1.0 = municipio de mayor riesgo del sistema. Auto-calibrado.

### Predicción — EWMA + Regresión lineal dual

```
slope_365d  → tendencia estructural anual (inmune a rebotes estacionales)
slope_90d   → momentum reciente
slope_blend = 0.65 × slope_365d + 0.35 × slope_90d

días_hasta_crítico = (umbral_15% - nivel_actual) / slope_365d
proyección[mes]    = nivel_actual + slope_blend × (mes × 30 días)
```

### Monitoreo en tiempo real — APScheduler

```
Al arrancar el servidor:
  precompute_trends() → slope EWMA(30d) por sensor → cache en memoria

Cada SENSOR_INTERVAL_MINUTES minutos:
  tick() → nivel(t+Δ) = nivel(t) + slope × Δt + ruido(σ=0.025m)
         → 51 nuevas lecturas insertadas en BD
```

---

## Por qué no promedio simple

| Municipio | AVG de sensores | Max-Pooling | Nivel reportado |
|---|---|---|---|
| Camiri (petrolero + urbano + ganadero) | 0.39 | **0.63** | crítico |
| San José (minero + urbano + reserva) | 0.24 | **0.25** | medio |
| Santa Cruz (5 zonas) | 0.16 | **0.17** | bajo |

El sensor petrolero de Camiri (1.84 m y bajando) queda visible aunque los otros sensores del municipio estén más estables.

---

## Documentación técnica

- [`docs/sensores-multi-sensor.md`](docs/sensores-multi-sensor.md) — arquitectura completa, fórmulas, ranking de municipios y referencia de archivos

---

## Equipo: NINJE

| Integrante | Rol |
|---|---|
| **Evert Rodríguez Araúz** | Backend Developer / Data Engineer |
| **Jael Mamani Sandoval** | Backend Developer / Data Engineer |
| **Douglas Ismael Rojas Rivero** | Frontend Developer |
| **Nataly Vanessa Martínez Martínez** | Frontend Developer |
| **Nicol Melany Guairaje Herbas** | Machine Learning Engineer |

---

*Proyecto desarrollado para la Hackathon Build With AI 2026 — Google Developer Groups NINJE*
