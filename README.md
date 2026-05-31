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
│   │   │   └── reading_controller.py
│   │   ├── dtos/                   # Data Transfer Objects (schemas Pydantic)
│   │   │   ├── alerta_dto.py
│   │   │   ├── municipio_dto.py
│   │   │   ├── prediccion_dto.py
│   │   │   └── reading_dto.py
│   │   ├── models/                 # Modelos ORM (SQLAlchemy)
│   │   │   ├── alerta_model.py
│   │   │   ├── municipio_model.py
│   │   │   └── reading_model.py
│   │   ├── repositories/           # Acceso a datos (patrón Repository)
│   │   │   ├── alerta_repository.py
│   │   │   ├── municipio_repository.py
│   │   │   └── reading_repository.py
│   │   ├── services/               # Lógica de negocio
│   │   │   ├── alerta_service.py
│   │   │   ├── gemini_service.py
│   │   │   ├── municipio_service.py
│   │   │   └── prediccion_service.py
│   │   ├── seeds/                  # Datos de prueba / mock data
│   │   │   ├── seed_data.py
│   │   │   └── seed_sensors.py
│   │   ├── config.py               # Configuración de la aplicación
│   │   ├── database.py             # Conexión y sesión con PostgreSQL
│   │   └── main.py                 # Punto de entrada FastAPI
│   ├── Dockerfile
│   ├── cloudbuild.yaml
│   └── requirements.txt
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
