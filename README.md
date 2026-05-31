# 💧 Acuífero-Data SCZ

## 📖 Información del Proyecto
Acuífero-Data SCZ es una plataforma de inteligencia hídrica diseñada para el monitoreo continuo y la predicción anticipada del estrés hídrico en los acuíferos subterráneos del departamento de Santa Cruz.

Mediante modelos de Machine Learning e Inteligencia Artificial Generativa, el sistema procesa datos meteorológicos y tasas de extracción para predecir sequías o desbordes con meses de anticipación, permitiendo a las autoridades tomar decisiones preventivas.

---

## 🏗️ Estructura del Proyecto

```
acuifero-data-backend/
├── backend/                        # API REST con FastAPI
│   ├── app/
│   │   ├── controllers/            # Endpoints y rutas HTTP
│   │   │   ├── alerta_controller.py
│   │   │   ├── gemini_controller.py
│   │   │   ├── municipio_controller.py
│   │   │   ├── prediccion_controller.py
│   │   │   ├── reading_controller.py
│   │   │   └── sensor_controller.py      # ← Multi-sensor: scores, live, sync
│   │   ├── dtos/                   # Data Transfer Objects (schemas Pydantic)
│   │   │   ├── alerta_dto.py
│   │   │   ├── municipio_dto.py
│   │   │   ├── prediccion_dto.py
│   │   │   ├── reading_dto.py
│   │   │   └── sensor_dto.py             # ← SensorScoreResponse, MunicipioSensorAggregation
│   │   ├── models/                 # Modelos ORM (SQLAlchemy)
│   │   │   ├── alerta_model.py
│   │   │   ├── municipio_model.py
│   │   │   ├── reading_model.py          # ← +sensor_id FK
│   │   │   └── sensor_model.py           # ← NUEVO: tabla sensores
│   │   ├── repositories/           # Acceso a datos (patrón Repository)
│   │   │   ├── alerta_repository.py
│   │   │   ├── municipio_repository.py
│   │   │   ├── reading_repository.py
│   │   │   └── sensor_repository.py      # ← NUEVO
│   │   ├── services/               # Lógica de negocio
│   │   │   ├── alerta_service.py
│   │   │   ├── gemini_service.py
│   │   │   ├── municipio_service.py
│   │   │   ├── prediccion_service.py
│   │   │   └── sensor_service.py         # ← EWMA scoring + Max-Pooling + Min-Max
│   │   ├── seeds/                  # Datos de prueba / mock data
│   │   │   ├── seed_data.py
│   │   │   ├── seed_sensors.py
│   │   │   └── seed_multi_sensor.py      # ← NUEVO: 51 sensores, 37k lecturas
│   │   ├── config.py               # Configuración de la aplicación
│   │   ├── database.py             # Conexión y sesión con PostgreSQL
│   │   └── main.py                 # Punto de entrada FastAPI
│   ├── Dockerfile
│   ├── cloudbuild.yaml
│   └── requirements.txt
│
├── docs/
│   └── sensores-multi-sensor.md   # ← Arquitectura y algoritmo multi-sensor
│
├── frontend/                       # SPA con Angular 21
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/
│   │   │   │   ├── models/
│   │   │   │   │   └── municipio.model.ts
│   │   │   │   └── services/
│   │   │   │       ├── alerta.ts           # Servicio de alertas
│   │   │   │       ├── api.ts              # Cliente HTTP base
│   │   │   │       ├── datos-locales.service.ts
│   │   │   │       ├── gemini.ts           # Integración con Gemini API
│   │   │   │       └── municipio.ts        # Servicio de municipios
│   │   │   ├── pages/
│   │   │   │   ├── dashboard/              # Dashboard principal con métricas
│   │   │   │   ├── landing/                # Página de inicio
│   │   │   │   └── municipio-detalle/      # Vista detalle por municipio
│   │   │   ├── shared/
│   │   │   │   └── components/
│   │   │   │       ├── alerta-card/        # Tarjeta de alertas hídricas
│   │   │   │       ├── gemini-panel/       # Panel de análisis con IA
│   │   │   │       ├── grafico-tendencia/  # Gráfico de tendencias históricas
│   │   │   │       ├── mapa-scz/           # Mapa interactivo de Santa Cruz
│   │   │   │       ├── navbar/             # Barra de navegación
│   │   │   │       └── stat-card/          # Tarjeta de estadísticas
│   │   │   ├── app.routes.ts               # Configuración de rutas
│   │   │   └── app.config.ts               # Configuración principal
│   │   ├── environments/
│   │   │   └── environment.ts              # Variables de entorno
│   │   ├── index.html
│   │   ├── main.ts
│   │   ├── main.server.ts                  # SSR entry point
│   │   ├── server.ts                       # Express server (SSR)
│   │   └── styles.css
│   ├── public/                             # Assets estáticos
│   ├── angular.json
│   ├── tailwind.config.js
│   └── package.json
│
├── docs/                           # Documentación técnica y arquitectura
├── scripts/                        # Scripts de generación de mock data
├── .gitignore
└── README.md
```

---

## 🚀 Tecnologías y Versiones

### Frontend
| Tecnología | Versión |
|---|---|
| Angular | 21.2.x |
| Tailwind CSS | 3.4.x |
| Leaflet.js | - |
| Chart.js | - |
| TypeScript | 5.x |

### Backend
| Tecnología | Versión |
|---|---|
| Python | 3.12 |
| FastAPI | 0.111.0 |
| Uvicorn | 0.29.0 |
| SQLAlchemy | 2.0.30 |
| Pydantic | 2.7.1 |
| Alembic | 1.13.1 |
| NumPy | ≥ 1.26.0 |
| Pandas | ≥ 2.2.0 |

### Base de Datos
| Tecnología | Versión |
|---|---|
| PostgreSQL | 18 |
| psycopg2-binary | 2.9.9 |

### Inteligencia Artificial
| Tecnología | Versión |
|---|---|
| Gemini API (google-generativeai) | 0.5.4 |
| Google Cloud AI Platform | ≥ 1.40.0 |
| Prophet | - |
| XGBoost | - |

---

## ⚙️ Instalación y Ejecución

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
La API estará disponible en: `http://localhost:8000`  
Documentación Swagger: `http://localhost:8000/docs`

### Poblar la base de datos

```bash
cd backend

# 1. Municipios y alertas iniciales
python -m app.seeds.seed_data

# 2. Sensores físicos (3–5 por municipio) + 2 años de lecturas diarias
python -m app.seeds.seed_multi_sensor

# 3. Calcular score_riesgo y nivel_riesgo desde los datos reales
curl -X POST "http://localhost:8000/sensores/sync-all?days=730"
```

> El paso 3 ejecuta el algoritmo EWMA Composite + Min-Max Cross-Normalization sobre los 51 sensores y persiste los resultados en la tabla `municipios`. Ver detalles en [`docs/sensores-multi-sensor.md`](docs/sensores-multi-sensor.md).

### Frontend
```bash
cd frontend
npm install
npm run start
```
La aplicación estará disponible en: `http://localhost:4200`

### Variables de Entorno (Backend)
Crear un archivo `.env` en `/backend`:
```env
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/acuifero_db
GEMINI_API_KEY=tu_api_key
```

---

## 🔬 Módulo Multi-Sensor y Algoritmo de Riesgo

El sistema implementa una arquitectura de monitoreo distribuido con **3–5 sensores físicos por municipio**, cada uno con comportamiento independiente según su zona (urbano, agrícola, minero, reserva, etc.).

### Pipeline de riesgo

1. **Ingesta**: lecturas diarias por sensor en tabla `readings` (51 sensores, 37 k lecturas/año)
2. **Evaluación individual**: algoritmo **EWMA Composite** — cruce de medias exponenciales (7d vs 90d) detecta caídas sostenidas distinguiéndolas de variación estacional
3. **Agregación por peor escenario**: **Max-Pooling** `= 0.7 × max(scores) + 0.3 × promedio_cuadrático` — un sensor en crisis no queda oculto por los demás
4. **Calibración relativa**: **Min-Max Cross-Normalization** con γ=0.5 entre todos los municipios — el score refleja posición relativa en el sistema
5. **Resultado**: un único `score_riesgo` (0–1) y `nivel_riesgo` (bajo/medio/alto/crítico) por municipio → Leaflet dibuja un círculo con el color correspondiente

### Por qué no AVG simple

| Escenario: 4 sensores en 0.2 + 1 en 0.9 | Resultado | Decisión |
|---|---|---|
| Promedio simple | 0.34 — medio | Alcalde no actúa |
| Max-Pooling (este sistema) | 0.87 — **crítico** | Alcalde recibe alerta |

Ver documentación completa: [`docs/sensores-multi-sensor.md`](docs/sensores-multi-sensor.md)

---

## 👥 Equipo: NINJE

| Integrante | Rol |
|---|---|
| **Evert Rodríguez Araúz** | Backend Developer / Data Engineer |
| **Jael Mamani Sandoval** | Backend Developer / Data Engineer |
| **Douglas Ismael Rojas Rivero** | Frontend Developer |
| **Nataly Vanessa Martínez Martínez** | Frontend Developer |
| **Nicol Melany Guairaje Herbas** | Machine Learning Engineer |

---

*Proyecto desarrollado para la Hackathon Build With AI 2026 - Google Developer Groups NINJE*
