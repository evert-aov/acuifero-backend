"""
Scheduler Service — Acuífero-Data SCZ
=======================================
Genera lecturas en tiempo real para todos los sensores activos.
Se ejecuta en background mediante APScheduler (BackgroundScheduler).

Pipeline por tick:
  1. Obtener última lectura de cada sensor
  2. Calcular delta usando la tendencia EWMA precalculada + estacionalidad + ruido
  3. Insertar nueva lectura con timestamp = ahora (UTC)

La tendencia EWMA se precalcula una vez al arrancar el servidor
a partir de los últimos 90 días de lecturas históricas.
Esto garantiza que Camiri siga bajando, Mineros siga estable, etc.

Configuración:
  SENSOR_INTERVAL_MINUTES (env, default=10) — frecuencia del tick
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd

from app.database import SessionLocal
from app.models.reading_model import Reading
from app.models.sensor_model import Sensor

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Estado global del scheduler
# ---------------------------------------------------------------------------

# Tendencia EWMA precalculada por sensor (m/día) — cargada al arranque
_trends: dict[int, float] = {}

# Estatus del scheduler para el endpoint /sensores/scheduler/status
_status = {
    "activo":         False,
    "ultimo_tick":    None,
    "lecturas_total": 0,
    "sensores":       0,
    "intervalo_min":  None,
}


# ---------------------------------------------------------------------------
# Precálculo de tendencias (ejecutado una vez al arranque)
# ---------------------------------------------------------------------------

def precompute_trends() -> None:
    """
    Calcula la pendiente EWMA(span=30) del nivel freático para cada sensor
    y la almacena en _trends. Se llama desde el lifespan de FastAPI.
    """
    db = SessionLocal()
    try:
        sensores = db.query(Sensor).filter(Sensor.activo == True).all()  # noqa: E712
        for s in sensores:
            # Últimas 90 lecturas del sensor
            rows = (
                db.query(Reading)
                .filter(Reading.sensor_id == s.id)
                .order_by(Reading.timestamp.desc())
                .limit(90)
                .all()
            )
            rows = list(reversed(rows))

            if len(rows) < 14:
                _trends[s.id] = 0.0
                continue

            niveles = pd.Series([r.nivel_freatico_m for r in rows], dtype=float)
            ewma    = niveles.ewm(span=30, adjust=False).mean()
            idx     = np.arange(len(ewma), dtype=float)
            slope   = float(np.polyfit(idx, ewma.values, 1)[0])
            _trends[s.id] = slope

        _status["sensores"] = len(_trends)
        log.info(
            "Tendencias precalculadas para %d sensores. "
            "Rango: [%.5f, %.5f] m/día",
            len(_trends),
            min(_trends.values(), default=0),
            max(_trends.values(), default=0),
        )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Generación de una lectura individual
# ---------------------------------------------------------------------------

def _generar_lectura(sensor: Sensor, ultima: Reading, ahora: datetime) -> Reading:
    """
    Genera la próxima lectura de un sensor a partir de la última existente.

    Modelo:
      nivel(t+dt) = nivel(t) + slope * dt_días + ruido_AR(1)
      precip(t)   = estacional * log-normal (zero-inflation en seca)
      humedad(t)  = suavizado estacional + ruido
      extrac(t)   = factor_sensor * variación_estacional + ruido
    """
    rng = np.random.default_rng()
    doy = ahora.timetuple().tm_yday
    phi = 2 * np.pi * (doy - 15.0) / 365.0

    # Tiempo desde la última lectura (días), limitado a 1 día
    ts_ultima = (
        ultima.timestamp
        if ultima.timestamp.tzinfo is not None
        else ultima.timestamp.replace(tzinfo=timezone.utc)
    )
    dt_days = min((ahora - ts_ultima).total_seconds() / 86400.0, 1.0)

    # ── Nivel freático ───────────────────────────────────────────────────
    slope      = _trends.get(sensor.id, 0.0)
    drift      = slope * dt_days
    noise      = float(rng.normal(0.0, 0.025))          # ±2.5 cm por lectura
    nuevo_nivel = float(np.clip(
        ultima.nivel_freatico_m + drift + noise,
        0.2, 50.0,
    ))

    # ── Precipitación ────────────────────────────────────────────────────
    dry_prob = float(np.clip(0.55 * np.cos(phi), 0.0, 0.70))
    if float(rng.random()) < dry_prob:
        nueva_precip = 0.0
    else:
        precip_base  = max(0.0, 12.0 * (1.0 - np.cos(phi)) / 2.0)
        nueva_precip = float(np.clip(
            precip_base * float(rng.lognormal(0.2, 0.55)),
            0.0, 80.0,
        ))

    # ── Humedad del suelo ────────────────────────────────────────────────
    hum_target = ultima.humedad_suelo_pct + 4.0 * (1.0 - np.cos(phi)) / 2.0
    nueva_hum  = float(np.clip(
        hum_target + float(rng.normal(0.0, 1.5)),
        10.0, 100.0,
    ))

    # ── Extracción ───────────────────────────────────────────────────────
    # Más alta en seca (cos > 0), modulada por el factor del sensor
    ext_season = sensor.factor_extrac * (1.0 + 0.12 * float(np.cos(phi)))
    nueva_ext  = float(np.clip(
        ultima.extraccion_lps * ext_season + float(rng.normal(0.0, ultima.extraccion_lps * 0.03)),
        ultima.extraccion_lps * 0.40,
        ultima.extraccion_lps * 1.85,
    ))

    return Reading(
        timestamp         = ahora,
        municipio_id      = sensor.municipio_id,
        sensor_id         = sensor.id,
        nivel_freatico_m  = round(nuevo_nivel, 3),
        humedad_suelo_pct = round(nueva_hum, 1),
        extraccion_lps    = round(nueva_ext, 2),
        precipitacion_mm  = round(nueva_precip, 2),
    )


# ---------------------------------------------------------------------------
# Tick del scheduler
# ---------------------------------------------------------------------------

def tick() -> int:
    """
    Genera una lectura nueva para cada sensor activo y la persiste en BD.
    Retorna el número de lecturas insertadas.

    APScheduler llama esta función cada SENSOR_INTERVAL_MINUTES minutos.
    Es segura para ejecución concurrente (max_instances=1 en el scheduler).
    """
    db = SessionLocal()
    count = 0
    try:
        ahora    = datetime.now(timezone.utc)
        sensores = db.query(Sensor).filter(Sensor.activo == True).all()  # noqa: E712

        nuevas = []
        for sensor in sensores:
            ultima = (
                db.query(Reading)
                .filter(Reading.sensor_id == sensor.id)
                .order_by(Reading.timestamp.desc())
                .first()
            )
            if ultima is None:
                continue
            nuevas.append(_generar_lectura(sensor, ultima, ahora))

        if nuevas:
            db.add_all(nuevas)
            db.commit()
            count = len(nuevas)

        _status["ultimo_tick"]    = ahora.isoformat()
        _status["lecturas_total"] += count
        log.info("Tick %s — %d lecturas generadas", ahora.strftime("%H:%M:%S UTC"), count)

    except Exception:
        db.rollback()
        log.exception("Error en scheduler tick.")
    finally:
        db.close()

    return count


# ---------------------------------------------------------------------------
# Estado público
# ---------------------------------------------------------------------------

def get_status() -> dict:
    return dict(_status)


def set_activo(activo: bool, intervalo: Optional[int] = None) -> None:
    _status["activo"] = activo
    if intervalo is not None:
        _status["intervalo_min"] = intervalo
