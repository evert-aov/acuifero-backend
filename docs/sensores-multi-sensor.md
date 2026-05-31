# Arquitectura Multi-Sensor y Algoritmo de Riesgo Hídrico

## Problema que resuelve

Un promedio simple (AVG) de múltiples sensores es peligroso en monitoreo hídrico. Si 4 sensores de un municipio están estables (score 0.2) y 1 está colapsando (score 0.9), el promedio devuelve 0.34 — clasificando el municipio como **medio** cuando una zona está en crisis real.

Este módulo implementa la arquitectura correcta: ingesta multi-sensor → evaluación individual → agregación por peor escenario → visualización ejecutiva.

---

## Arquitectura del pipeline

```
Sensores físicos (3–5 por municipio)
         │
         ▼
  Lecturas diarias en BD (tabla readings con sensor_id)
         │
         ▼
  EWMA Composite Score por sensor   ← O(n) sin entrenamiento
         │
         ▼
  Max-Pooling ponderado por municipio
         │
         ▼
  Min-Max Cross-Normalization entre municipios   ← calibración relativa
         │
         ▼
  score_riesgo + nivel_riesgo en BD (municipios)
         │
         ▼
  API → Leaflet dibuja 1 círculo por municipio (color = nivel_riesgo)
```

---

## Modelo de datos

### Tabla `sensores`

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | |
| `municipio_id` | INTEGER FK | Municipio al que pertenece |
| `nombre` | VARCHAR | Ej. "Sensor 2 — Minero Norte" |
| `zona` | VARCHAR | urbano, periurbano, agricola, minero, reserva, etc. |
| `lat` / `lng` | FLOAT | Coordenadas físicas del sensor |
| `offset_nivel` | FLOAT | Desviación del nivel base del municipio (m) |
| `factor_extrac` | FLOAT | Multiplicador de extracción respecto al base |
| `activo` | BOOLEAN | |

### Cambio en tabla `readings`

Se agrega la columna `sensor_id` (nullable FK a `sensores`). Las lecturas históricas del seed original quedan con `sensor_id = NULL`; las del seed multi-sensor tienen `sensor_id` poblado.

---

## Algoritmo de scoring: EWMA Composite

### Por qué EWMA

El Exponential Weighted Moving Average (EWMA) es el estándar en monitoreo industrial/IoT:

- Da más peso a lecturas recientes sin descartar la memoria histórica.
- El **cruce entre EWMA rápida (span=7 días) y lenta (span=90 días)** detecta exactamente cuándo un acuífero entra en caída sostenida, distinguiéndola de la variación estacional normal (ej. rebote de lluvias en enero no oculta una tendencia de 2 años de descenso).
- Complejidad O(n), determinista, sin entrenamiento.

### Fórmula por sensor

```
score_raw = 0.35 × agotamiento
          + 0.30 × cruce_ewma
          + 0.20 × velocidad_ewma
          + 0.15 × presion_extraccion
```

| Componente | Cálculo | Qué captura |
|---|---|---|
| **Agotamiento** | `1 - EWMA_7d(nivel) / max_historico` | Qué tan cerca del fondo está el acuífero |
| **Cruce EWMA** | `(EWMA_90d - EWMA_7d) / σ_nivel` normalizado a 3σ | Caída sostenida vs fluctuación estacional |
| **Velocidad EWMA** | Pendiente de EWMA_90d en últimos 30 días | Si el deterioro se está acelerando |
| **Presión extracción** | `EWMA_7d(extracción) / max_extracción` | Si la bomba opera al límite hoy |

### Por qué no promedio simple para el cruce

El cruce EWMA se normaliza por la desviación estándar del nivel (`σ`) del mismo sensor. Esto permite comparar acuíferos de distintas magnitudes (uno con base 7 m vs otro con base 25 m) usando la misma escala de riesgo.

---

## Agregación por municipio: Max-Pooling ponderado

```python
score_municipio = 0.7 × max(scores_sensores)
                + 0.3 × promedio_cuadrático(scores_sensores)
```

El **promedio cuadrático** (peso = score²) da más influencia a los sensores de mayor riesgo dentro del promedio. Combinado con el 70% de peso al máximo, garantiza que un sensor en crisis sea visible en el score final del municipio.

**Demostración:**

| Escenario | AVG simple | Max-Pooling | Decisión alcalde |
|---|---|---|---|
| 4 × 0.2 + 1 × 0.9 | 0.34 (medio) | **0.87 (crítico)** | Con AVG no actúa; con Max-Pool recibe alerta |

---

## Normalización cruzada: Min-Max con γ=0.5

Una vez calculado el `score_raw` de cada municipio, se aplica normalización Min-Max entre todos los municipios del sistema:

```
score_normalizado = ((score_raw - min_global) / (max_global - min_global)) ^ 0.5
```

**Por qué γ=0.5 (raíz cuadrada):**
- Estira la distribución hacia la zona media, dando más resolución donde las decisiones importan.
- Separa correctamente los 4 niveles de riesgo (bajo/medio/alto/crítico) para el conjunto actual de municipios.

**Semántica del score normalizado:**
- `1.0` = el municipio de mayor riesgo del sistema.
- `0.0` = el de menor riesgo.
- Los umbrales son relativos, auto-calibrados: si todo el sistema mejora, los scores bajan solos.

### Umbrales de clasificación

| Score normalizado | Nivel | Color en mapa |
|---|---|---|
| ≥ 0.75 | `critico` | Rojo pulsante |
| ≥ 0.50 | `alto` | Naranja |
| ≥ 0.25 | `medio` | Amarillo |
| < 0.25 | `bajo` | Verde |

---

## Ranking actual del sistema (basado en datos reales de sensores)

| Municipio | Score normalizado | Nivel |
|---|---|---|
| Camiri | 1.0000 | crítico |
| Charagua | 0.6396 | alto |
| San José de Chiquitos | 0.6064 | alto |
| Cabezas | 0.5964 | alto |
| San Ramón | 0.3099 | medio |
| Concepción | 0.2906 | medio |
| San Ignacio de Velasco | 0.2606 | medio |
| Vallegrande | 0.2476 | bajo |
| Santa Cruz de la Sierra | 0.2095 | bajo |
| Montero | 0.2085 | bajo |
| Samaipata | 0.1715 | bajo |
| Warnes | 0.1238 | bajo |
| Portachuelo | 0.1038 | bajo |
| Mineros | 0.0734 | bajo |
| Puerto Suárez | 0.0000 | bajo |

---

## Endpoints de la API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/sensores/{municipio_id}` | Lista sensores activos del municipio |
| GET | `/sensores/{municipio_id}/scores?days=730` | Score individual por sensor + score agregado Max-Pooling |
| GET | `/sensores/{municipio_id}/live` | Lectura en tiempo real de todos los sensores (con ruido simulado ±2%) |
| POST | `/sensores/{municipio_id}/sync-score` | Recalcula score de un municipio (sin normalización cruzada) |
| POST | `/sensores/sync-all?days=730` | **Recalcula todos los municipios** con EWMA + Min-Max. Reemplaza los valores hardcodeados del seed |

### Respuesta de `/sensores/{id}/scores`

```json
{
  "municipio_id": 10,
  "score_agregado": 1.0,
  "nivel_riesgo": "critico",
  "sensor_critico": {
    "sensor_id": 35,
    "nombre": "Sensor 2 — Petrolero",
    "zona": "petrolero",
    "score": 0.6417,
    "nivel_freatico_m": 1.84,
    "tendencia_m_dia": 0.000695,
    "nivel_riesgo": "alto",
    "timestamp": "2026-05-31T00:00:00Z"
  },
  "sensores": [...]
}
```

---

## Seeds

### `seed_data.py`

Pobla municipios y alertas iniciales. **No hardcodea** `score_riesgo` ni `nivel_riesgo` — los deja en los valores por defecto del modelo (0.0 / "bajo"). Los scores reales se calculan con `sync_all_scores`.

### `seed_multi_sensor.py`

Genera 3–5 sensores físicos por municipio con parámetros diferenciados por zona (urbano, agrícola, minero, reserva, etc.) y 730 días de lecturas históricas diarias por sensor.

```bash
# Ejecución completa desde cero
cd backend
python -m app.seeds.seed_data
python -m app.seeds.seed_multi_sensor
# Luego: POST http://localhost:8000/sensores/sync-all?days=730
```

### Sensores por municipio

| Municipio | N° sensores | Zonas simuladas |
|---|---|---|
| Santa Cruz de la Sierra | 5 | urbano_central, periurbano_norte, agricola_este, reserva_oeste, industrial_sur |
| Charagua | 3 | urbano, agricola_norte, ganadero_sur |
| Cabezas | 3 | urbano, agricola, periurbano |
| San Ignacio de Velasco | 4 | urbano, turismo_norte, agricola, ganadero |
| San José de Chiquitos | 4 | urbano, **minero_norte**, agricola, reserva |
| Camiri | 3 | urbano, **petrolero**, ganadero |
| Montero | 4 | urbano, industrial, agricola, periurbano |
| Resto | 3 | urbano, agricola/uso_local, zona_natural |

Los sensores en zonas extractivas (minero, petrolero, industrial) tienen `factor_extrac` mayor y `offset_nivel` negativo, simulando la sobreexplotación localizada.

---

## Archivos modificados/creados

```
backend/app/
├── models/
│   ├── reading_model.py        # + columna sensor_id (FK nullable)
│   └── sensor_model.py         # NUEVO: modelo Sensor
├── dtos/
│   └── sensor_dto.py           # NUEVO: SensorResponse, SensorScoreResponse, MunicipioSensorAggregation
├── repositories/
│   └── sensor_repository.py    # NUEVO: consultas por sensor
├── services/
│   └── sensor_service.py       # NUEVO: EWMA scoring, Max-Pooling, Min-Max normalization
├── controllers/
│   └── sensor_controller.py    # NUEVO: endpoints /sensores/...
└── seeds/
    ├── seed_data.py             # Eliminados score_riesgo/nivel_riesgo hardcodeados
    └── seed_multi_sensor.py    # NUEVO: generador multi-sensor
```
