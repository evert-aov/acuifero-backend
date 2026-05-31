"""
Sensor Service — Acuífero-Data SCZ
====================================
Evalúa el riesgo individual de cada sensor y agrega los scores
usando Max-Pooling ponderado.

Algoritmo de scoring: EWMA Composite + Min-Max Cross-Normalization
------------------------------------------------------------------
Por qué EWMA (Exponential Weighted Moving Average):
  - Suaviza el ruido diario sin perder memoria de la tendencia.
  - El cruce de EWMA rápida (7d) vs lenta (90d) detecta exactamente
    cuándo un acuífero empieza una caída sostenida vs variación estacional.
  - Es el estándar en monitoreo industrial/IoT (control charts).
  Complejidad: O(n) por serie, sin entrenamiento.

Por qué Min-Max Cross-Normalization:
  - Score relativo: 0.91 en Camiri significa "peor 9% de los municipios
    monitoreados", no un número absoluto sin referencia.
  - Auto-calibrado: si mejora todo el sistema, los scores bajan solos.
  - Se aplica solo en `sync_all_scores`, que corre en batch.

Lógica de agregación (por qué no AVG simple):
  Si 4 sensores están estables (score 0.2) y 1 está colapsando (0.9),
  el promedio daría 0.34 (bajo) — ocultando la crisis real.
  Max-Pooling: 0.7 * max(scores) + 0.3 * promedio_cuadrático(scores)
  → resultado: ≈ 0.69 (alto), reflejando el sensor crítico.
"""

from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.reading_model import Reading
from app.repositories.sensor_repository import SensorRepository
from app.repositories.municipio_repository import MunicipioRepository
from app.dtos.sensor_dto import SensorScoreResponse, MunicipioSensorAggregation

_repo    = SensorRepository()

# Umbrales para clasificar nivel de riesgo desde score normalizado
_NIVEL_UMBRALES = [
    (0.75, "critico"),
    (0.50, "alto"),
    (0.25, "medio"),
    (0.00, "bajo"),
]


def _score_to_nivel(score: float) -> str:
    for threshold, nivel in _NIVEL_UMBRALES:
        if score >= threshold:
            return nivel
    return "bajo"


# ---------------------------------------------------------------------------
# Score individual de un sensor — EWMA Composite
# ---------------------------------------------------------------------------

def _calcular_score_sensor(readings: list[Reading]) -> tuple[float, float]:
    """
    Devuelve (score_raw, velocidad_m_dia).

    Algoritmo: EWMA Composite (4 componentes, O(n)):

      35% — Agotamiento: (1 - EWMA_rapida / pico_historico)
             EWMA 7d del nivel vs el pico máximo de la serie.
             Detecta qué tan cercano al fondo está el acuífero.

      30% — Cruce EWMA: (EWMA_lenta - EWMA_rapida) / σ_nivel
             Cuando la media rápida cae bajo la lenta, el acuífero
             lleva tiempo en descenso. Normalizado por desv. estándar
             para comparar acuíferos de distintas magnitudes (2m vs 25m).

      20% — Velocidad EWMA: pendiente de EWMA_lenta en últimos 30 días.
             Captura si el deterioro se está acelerando o estabilizando.

      15% — Presión de extracción: EWMA_7d_extracción / pico_extracción.
             Mide qué tan cerca del máximo opera la bomba hoy.

    El score_raw es absoluto (no normalizado entre municipios).
    La normalización cruzada ocurre en sync_all_scores().
    """
    if not readings:
        return 0.0, 0.0

    niveles = pd.Series([r.nivel_freatico_m for r in readings], dtype=float)
    extracc = pd.Series([r.extraccion_lps   for r in readings], dtype=float)

    # --- EWMA del nivel: rápida (7d) y lenta (90d)
    ewma_fast = niveles.ewm(span=7,  adjust=False).mean()
    ewma_slow = niveles.ewm(span=90, adjust=False).mean()

    # --- Componente 1: agotamiento
    pico             = niveles.max()
    current_fast     = float(ewma_fast.iloc[-1])
    agotamiento      = (1.0 - current_fast / pico) if pico > 0 else 0.0
    agotamiento_score = min(max(agotamiento, 0.0), 1.0)

    # --- Componente 2: cruce EWMA (lenta - rápida normalizado por σ)
    sigma = float(niveles.std()) or 1.0
    cruce = float(ewma_slow.iloc[-1] - ewma_fast.iloc[-1]) / sigma
    # 3σ de divergencia → score 1.0 (acuífero en caída sostenida)
    cruce_score = min(max(cruce / 3.0, 0.0), 1.0)

    # --- Componente 3: velocidad de EWMA_lenta (últimos 30 días)
    ewma_reciente = ewma_slow.iloc[-30:].to_numpy()
    idx           = np.arange(len(ewma_reciente), dtype=float)
    velocidad = float(np.polyfit(idx, ewma_reciente, 1)[0]) if len(ewma_reciente) > 1 else 0.0
    # -0.008 m/día (≈ -3 m/año) → score 1.0
    velocidad_score = min(abs(min(velocidad, 0.0)) / 0.008, 1.0)

    # --- Componente 4: presión de extracción (EWMA 7d)
    ewma_extrac  = extracc.ewm(span=7, adjust=False).mean()
    pico_extrac  = float(extracc.max()) or 1.0
    extrac_score = min(float(ewma_extrac.iloc[-1]) / pico_extrac, 1.0)

    score = (
        0.35 * agotamiento_score
        + 0.30 * cruce_score
        + 0.20 * velocidad_score
        + 0.15 * extrac_score
    )
    return round(min(score, 1.0), 4), round(velocidad, 6)


# ---------------------------------------------------------------------------
# Normalización cruzada Min-Max entre municipios
# ---------------------------------------------------------------------------

def _minmax_normalizar(raw_scores: dict[int, float]) -> dict[int, float]:
    """
    Escala los scores brutos al rango [0, 1] usando Min-Max.

    score_final = (raw - min) / (max - min)

    Semántica: 1.0 = el municipio de mayor riesgo del sistema;
               0.0 = el de menor riesgo.
    Aplica γ=0.8 para dar más resolución en la zona alta de riesgo
    (donde las decisiones importan más).
    """
    if len(raw_scores) < 2:
        return raw_scores

    vals = list(raw_scores.values())
    vmin, vmax = min(vals), max(vals)
    rango = vmax - vmin or 1.0

    # γ=0.5 (raíz cuadrada): spread óptimo — separa bien critico/alto/medio/bajo
    return {
        mun_id: float(round(((raw - vmin) / rango) ** 0.5, 4))
        for mun_id, raw in raw_scores.items()
    }


# ---------------------------------------------------------------------------
# Agregación Max-Pooling por municipio
# ---------------------------------------------------------------------------

def _max_pool_scores(scores: list[float]) -> float:
    """
    Devuelve el score agregado de un municipio dado los scores individuales.

    Fórmula: 0.7 * max(scores) + 0.3 * promedio_cuadrático(scores)
    El promedio cuadrático da más peso a los sensores de mayor riesgo.
    """
    if not scores:
        return 0.0
    max_score = max(scores)
    # Promedio ponderado cuadráticamente (w_i = score_i^2)
    weights   = [s ** 2 for s in scores]
    total_w   = sum(weights)
    if total_w == 0:
        weighted_avg = 0.0
    else:
        weighted_avg = sum(s * w for s, w in zip(scores, weights)) / total_w
    return round(0.70 * max_score + 0.30 * weighted_avg, 4)


# ---------------------------------------------------------------------------
# Lectura "en vivo" simulada para un sensor
# ---------------------------------------------------------------------------

def _live_reading(last: Reading) -> Reading:
    """
    A partir de la última lectura real, aplica ruido aleatorio para simular
    la variación en tiempo real (±1-3% por variable).
    """
    rng = np.random.default_rng()
    fake = Reading(
        timestamp         = datetime.now(timezone.utc),
        municipio_id      = last.municipio_id,
        sensor_id         = last.sensor_id,
        nivel_freatico_m  = round(last.nivel_freatico_m  * rng.uniform(0.98, 1.02), 3),
        humedad_suelo_pct = round(last.humedad_suelo_pct * rng.uniform(0.97, 1.03), 1),
        extraccion_lps    = round(last.extraccion_lps    * rng.uniform(0.96, 1.04), 2),
        precipitacion_mm  = round(max(0.0, last.precipitacion_mm * rng.uniform(0.9, 1.1)), 2),
    )
    return fake


# ---------------------------------------------------------------------------
# Servicio público
# ---------------------------------------------------------------------------

class SensorService:
    def __init__(self, db: Session):
        self.db         = db
        self.mun_repo   = MunicipioRepository(db)

    # ── 1. Score de todos los sensores de un municipio ──────────────────────

    def get_scores_por_municipio(
        self, municipio_id: int, days: int = 90
    ) -> MunicipioSensorAggregation:
        sensores = _repo.get_by_municipio(self.db, municipio_id)

        scored: list[SensorScoreResponse] = []
        for sensor in sensores:
            readings = _repo.get_readings(self.db, sensor.id, days=days)
            score, tendencia = _calcular_score_sensor(readings)

            last_r   = readings[-1] if readings else None
            ts       = last_r.timestamp if last_r else datetime.now(timezone.utc)
            nivel    = last_r.nivel_freatico_m if last_r else 0.0

            scored.append(SensorScoreResponse(
                sensor_id        = sensor.id,
                nombre           = sensor.nombre,
                zona             = sensor.zona,
                lat              = sensor.lat,
                lng              = sensor.lng,
                score            = score,
                nivel_freatico_m = nivel,
                tendencia_m_dia  = tendencia,
                nivel_riesgo     = _score_to_nivel(score),
                timestamp        = ts,
            ))

        scores_vals = [s.score for s in scored]
        score_agg   = _max_pool_scores(scores_vals)
        critico     = max(scored, key=lambda s: s.score) if scored else None

        return MunicipioSensorAggregation(
            municipio_id   = municipio_id,
            score_agregado = score_agg,
            nivel_riesgo   = _score_to_nivel(score_agg),
            sensores       = scored,
            sensor_critico = critico,
        )

    # ── 2. Lectura en tiempo real de todos los sensores de un municipio ─────

    def get_live_municipio(self, municipio_id: int) -> list[dict]:
        sensores = _repo.get_by_municipio(self.db, municipio_id)
        result   = []
        for sensor in sensores:
            last = _repo.get_last_reading(self.db, sensor.id)
            if last is None:
                continue
            live  = _live_reading(last)
            score, tendencia = _calcular_score_sensor(
                _repo.get_readings(self.db, sensor.id, days=30)
            )
            result.append({
                "sensor_id":         sensor.id,
                "nombre":            sensor.nombre,
                "zona":              sensor.zona,
                "lat":               sensor.lat,
                "lng":               sensor.lng,
                "timestamp":         live.timestamp,
                "nivel_freatico_m":  live.nivel_freatico_m,
                "humedad_suelo_pct": live.humedad_suelo_pct,
                "extraccion_lps":    live.extraccion_lps,
                "precipitacion_mm":  live.precipitacion_mm,
                "score":             score,
                "tendencia_m_dia":   tendencia,
                "nivel_riesgo":      _score_to_nivel(score),
            })
        return result

    # ── 3. Actualizar score de UN municipio en la BD ────────────────────────

    def sync_municipio_score(self, municipio_id: int) -> None:
        """Recalcula y persiste el score de un municipio (sin normalización cruzada)."""
        agg = self.get_scores_por_municipio(municipio_id)
        mun = self.mun_repo.get_by_id(municipio_id)
        if mun is None:
            return
        mun.score_riesgo = agg.score_agregado
        mun.nivel_riesgo = agg.nivel_riesgo
        self.db.commit()

    # ── 4. Recalcular TODOS los municipios con normalización cruzada ─────────

    def sync_all_scores(self, days: int = 730) -> list[dict]:
        """
        Recalcula score_riesgo y nivel_riesgo de todos los municipios con sensores,
        aplicando normalización Min-Max cruzada para que los scores sean relativos.

        Pipeline:
          1. Para cada municipio → EWMA composite score de cada sensor
          2. Max-Pooling → score_raw del municipio
          3. Min-Max normalización entre todos los municipios
          4. Persistir en BD

        O(M * S * N) donde M=municipios, S=sensores, N=días de lecturas.
        Sin entrenamiento, determinista, reproducible.
        """
        municipios = self.mun_repo.get_all()
        raw_scores: dict[int, float] = {}

        for mun in municipios:
            sensores = _repo.get_by_municipio(self.db, mun.id)
            if not sensores:
                continue
            sensor_scores = []
            for s in sensores:
                readings = _repo.get_readings(self.db, s.id, days=days)
                score, _ = _calcular_score_sensor(readings)
                sensor_scores.append(score)
            raw_scores[mun.id] = _max_pool_scores(sensor_scores)

        normalized = _minmax_normalizar(raw_scores)

        resultado = []
        for mun in municipios:
            if mun.id not in normalized:
                continue
            score = normalized[mun.id]
            nivel = _score_to_nivel(score)
            mun.score_riesgo = score
            mun.nivel_riesgo = nivel
            resultado.append({
                "municipio_id":   mun.id,
                "nombre":         mun.nombre,
                "score_raw":      raw_scores[mun.id],
                "score_riesgo":   score,
                "nivel_riesgo":   nivel,
            })

        self.db.commit()
        return sorted(resultado, key=lambda r: r["score_riesgo"], reverse=True)
