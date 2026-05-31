"""
Mock Sensor Generator — Acuífero-Data SCZ
==========================================
Genera 2 años de lecturas diarias simuladas (frecuencia: 1/día) para cada
municipio registrado en la base de datos y las inserta de forma masiva en
la tabla `readings`.

Patrones simulados
------------------
  - Estacionalidad anual (seno/coseno): lluvias nov-mar, seca may-oct
  - Tendencia de sobreexplotación (nivel freático negativo) en municipios críticos
  - Eventos extremos de lluvia torrencial de 3-4 días (riesgo de desborde)

Uso
---
  cd acuifero-data-backend
  python -m app.seeds.seed_sensors               # elimina lecturas previas
  python -m app.seeds.seed_sensors --no-clear    # agrega sin borrar
"""

import argparse
import logging
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sqlalchemy import text

from app.database import SessionLocal, engine, Base
from app.models.reading_model import Reading          # crea tabla si no existe
from app.models.municipio_model import Municipio      # noqa: F401 — FK dependency

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)-8s]  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes globales
# ---------------------------------------------------------------------------
TWO_YEARS_DAYS = 730
BATCH_SIZE     = 5_000
RNG_SEED       = 42

# IDs con tendencia negativa comprobada (sobreexplotación)
OVEREXPLOITATION_IDS: set[int] = {2, 3, 6, 10}

# ---------------------------------------------------------------------------
# Parámetros por municipio
# Columnas:
#   base_nivel      → nivel freático base en metros (profundidad media)
#   nivel_amp       → amplitud estacional del nivel (m)
#   base_humedad    → humedad suelo base (%)
#   base_extraccion → extracción base en litros/segundo
#   trend_m_day     → tendencia lineal del nivel freático (m/día, negativo = descenso)
#   rain_factor     → multiplicador de precipitación relativo a SCZ=1.0
# ---------------------------------------------------------------------------
# fmt: off
MUNICIPIO_PARAMS: dict[int, dict] = {
    1:  {"base_nivel": 18.0, "nivel_amp": 2.2, "base_humedad": 55, "base_extraccion": 420,  "trend_m_day":  0.000,  "rain_factor": 1.00},  # SCZ
    2:  {"base_nivel":  8.5, "nivel_amp": 1.0, "base_humedad": 38, "base_extraccion": 95,   "trend_m_day": -0.0033, "rain_factor": 0.60},  # Charagua
    3:  {"base_nivel":  9.0, "nivel_amp": 1.1, "base_humedad": 40, "base_extraccion": 88,   "trend_m_day": -0.0030, "rain_factor": 0.65},  # Cabezas
    4:  {"base_nivel": 14.0, "nivel_amp": 1.8, "base_humedad": 52, "base_extraccion": 130,  "trend_m_day": -0.0008, "rain_factor": 0.90},  # San Ignacio
    5:  {"base_nivel": 15.0, "nivel_amp": 1.9, "base_humedad": 54, "base_extraccion": 110,  "trend_m_day": -0.0006, "rain_factor": 0.90},  # Concepción
    6:  {"base_nivel": 12.0, "nivel_amp": 1.4, "base_humedad": 50, "base_extraccion": 140,  "trend_m_day": -0.0042, "rain_factor": 0.85},  # San José de Chiquitos
    7:  {"base_nivel": 20.0, "nivel_amp": 2.5, "base_humedad": 60, "base_extraccion": 310,  "trend_m_day": -0.0008, "rain_factor": 1.10},  # Montero
    8:  {"base_nivel": 19.5, "nivel_amp": 2.3, "base_humedad": 58, "base_extraccion": 265,  "trend_m_day": -0.0007, "rain_factor": 1.05},  # Warnes
    9:  {"base_nivel": 22.0, "nivel_amp": 2.7, "base_humedad": 62, "base_extraccion": 230,  "trend_m_day":  0.0000, "rain_factor": 1.15},  # Mineros
    10: {"base_nivel":  7.0, "nivel_amp": 0.8, "base_humedad": 32, "base_extraccion": 145,  "trend_m_day": -0.0060, "rain_factor": 0.50},  # Camiri
    11: {"base_nivel": 21.0, "nivel_amp": 2.4, "base_humedad": 61, "base_extraccion": 135,  "trend_m_day":  0.0000, "rain_factor": 1.10},  # Portachuelo
    12: {"base_nivel": 13.5, "nivel_amp": 1.6, "base_humedad": 51, "base_extraccion": 56,   "trend_m_day": -0.0008, "rain_factor": 0.88},  # San Ramón
    13: {"base_nivel": 16.0, "nivel_amp": 1.7, "base_humedad": 48, "base_extraccion": 95,   "trend_m_day": -0.0007, "rain_factor": 0.80},  # Vallegrande
    14: {"base_nivel": 17.0, "nivel_amp": 1.8, "base_humedad": 50, "base_extraccion": 42,   "trend_m_day":  0.0000, "rain_factor": 0.85},  # Samaipata
    15: {"base_nivel": 25.0, "nivel_amp": 3.0, "base_humedad": 70, "base_extraccion": 72,   "trend_m_day":  0.0000, "rain_factor": 1.30},  # Puerto Suárez
}
# fmt: on


# ---------------------------------------------------------------------------
# Helpers de señal
# ---------------------------------------------------------------------------

def _seasonal_phase(doy: np.ndarray) -> np.ndarray:
    """
    Fase anual alineada con el calendario boliviano.
    Coseno negativo en la cima de la época húmeda (≈ 15 de enero, doy=15).
    Resultado: 0 en pico de lluvias, π en pico de sequía.
    """
    return 2 * np.pi * (doy - 15.0) / 365.0


def _inject_extreme_events(
    precipitacion: np.ndarray,
    n_days: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Inserta entre 9 y 14 eventos de lluvia torrencial (≈5-7 por año).
    Devuelve (precipitacion_modificada, mascara_bool_de_extremos).
    """
    n_events = int(rng.integers(9, 15))
    starts   = rng.integers(0, n_days - 4, size=n_events)
    mask     = np.zeros(n_days, dtype=bool)
    for s in starts:
        length = int(rng.integers(3, 5))
        mask[s : s + length] = True
    precipitacion = precipitacion.copy()
    precipitacion[mask] = rng.uniform(80, 160, size=int(mask.sum()))
    return precipitacion, mask


# ---------------------------------------------------------------------------
# Generación vectorizada por municipio
# ---------------------------------------------------------------------------

def generate_readings(
    municipio_id: int,
    params: dict,
    date_range: pd.DatetimeIndex,
    rng: np.random.Generator,
) -> pd.DataFrame:
    n    = len(date_range)
    days = np.arange(n, dtype=float)
    doy  = date_range.day_of_year.to_numpy(dtype=float)
    phi  = _seasonal_phase(doy)  # 0 en enero, π en julio

    rf = params["rain_factor"]

    # ------------------------------------------------------------------
    # Precipitación (mm/día)
    # Base estacional: coseno rebatido → 0 en seca, máximo en lluvias
    # ------------------------------------------------------------------
    precip_base = 30.0 * rf * (1.0 - np.cos(phi)) / 2.0   # 0..30*rf mm/día
    noise_mult  = rng.lognormal(mean=0.3, sigma=0.7, size=n)
    precip_raw  = precip_base * noise_mult

    # Zero-inflation en época seca (cos > 0.2 → tendencia a días sin lluvia)
    dry_prob = np.clip(0.55 * np.cos(phi), 0.0, 0.75)
    dry_days = rng.random(n) < dry_prob
    precip_raw[dry_days] = 0.0
    precip_raw = np.clip(precip_raw, 0.0, 100.0)

    # Eventos extremos (tormentas torrenciales)
    precipitacion, extreme_mask = _inject_extreme_events(precip_raw, n, rng)

    # ------------------------------------------------------------------
    # Humedad del suelo (%)
    # Sigue a la estacionalidad + acumulación de precipitación (media 7d)
    # ------------------------------------------------------------------
    base_h     = params["base_humedad"]
    hum_season = base_h + 22.0 * (1.0 - np.cos(phi)) / 2.0   # +22pp en pico húmedo

    precip_ma7 = (
        pd.Series(precipitacion).rolling(7, min_periods=1).mean().to_numpy()
    )
    hum_boost = np.clip(precip_ma7 * 0.30, 0.0, 28.0)

    humedad = hum_season + hum_boost + rng.normal(0.0, 2.0, n)
    humedad[extreme_mask] = rng.uniform(92.0, 100.0, size=int(extreme_mask.sum()))
    humedad = np.clip(humedad, 10.0, 100.0)

    # ------------------------------------------------------------------
    # Extracción (litros/segundo)
    # Más alta en época seca; pequeña variación diaria operacional
    # ------------------------------------------------------------------
    base_e = params["base_extraccion"]
    ext_season = base_e * (1.0 + 0.28 * np.cos(phi))         # +28% en seca
    ext_jitter = rng.normal(0.0, base_e * 0.04, n)
    extraccion = np.clip(ext_season + ext_jitter, base_e * 0.45, base_e * 1.85)

    # ------------------------------------------------------------------
    # Nivel freático (m)
    # Estacional + tendencia lineal + ruido AR(1) + recarga diferida
    # ------------------------------------------------------------------
    base_n = params["base_nivel"]
    amp_n  = params["nivel_amp"]

    nivel_season = base_n + amp_n * (1.0 - np.cos(phi)) / 2.0
    trend        = params["trend_m_day"] * days

    # Ruido correlacionado (suavizado exponencial sobre ruido blanco)
    white = rng.normal(0.0, 0.045, n)
    ar1   = pd.Series(white).ewm(span=14, adjust=False).mean().to_numpy()

    # Recarga del acuífero: precipitación acumulada con retardo ~10 días
    recharge = (
        pd.Series(precipitacion).rolling(10, min_periods=1).mean().to_numpy()
    )
    nivel = nivel_season + trend + ar1 + recharge * 0.016
    nivel = np.clip(nivel, 0.5, 45.0)

    return pd.DataFrame(
        {
            "timestamp":         date_range,
            "municipio_id":      np.int32(municipio_id),
            "precipitacion_mm":  np.round(precipitacion, 2),
            "humedad_suelo_pct": np.round(humedad, 1),
            "extraccion_lps":    np.round(extraccion, 2),
            "nivel_freatico_m":  np.round(nivel, 3),
        }
    )


# ---------------------------------------------------------------------------
# Inserción masiva
# ---------------------------------------------------------------------------

def _insert_batch(session, records: list[dict]) -> None:
    session.execute(Reading.__table__.insert(), records)
    session.commit()


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def seed_sensors(clear_existing: bool = True) -> None:
    log.info("=" * 60)
    log.info("  Mock Sensor Generator — Acuífero-Data SCZ")
    log.info("=" * 60)

    # Crea la tabla readings si no existe (idempotente)
    Base.metadata.create_all(bind=engine)
    log.info("Tabla 'readings' verificada/creada en la base de datos.")

    # Rango temporal: últimos 2 años hasta hoy (UTC, frecuencia diaria)
    end_dt    = datetime.now(tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start_dt  = end_dt - pd.Timedelta(days=TWO_YEARS_DAYS - 1)
    date_range = pd.date_range(start=start_dt, end=end_dt, freq="D", tz="UTC")
    log.info(
        "Rango: %s → %s  (%d días)",
        start_dt.date(), end_dt.date(), len(date_range),
    )

    rng = np.random.default_rng(RNG_SEED)

    session = SessionLocal()
    try:
        if clear_existing:
            n_deleted = session.execute(text("DELETE FROM readings")).rowcount
            session.commit()
            log.info("Lecturas previas eliminadas: %d registros.", n_deleted)

        total = 0
        for mun_id, params in MUNICIPIO_PARAMS.items():
            trend_label = (
                f"↓ {abs(params['trend_m_day'])*365:.2f} m/año"
                if params["trend_m_day"] < 0
                else "estable"
            )
            log.info(
                "Generando  municipio_id=%-3d  trend=%-20s  ...",
                mun_id, trend_label,
            )
            df      = generate_readings(mun_id, params, date_range, rng)
            records = df.to_dict(orient="records")

            for i in range(0, len(records), BATCH_SIZE):
                _insert_batch(session, records[i : i + BATCH_SIZE])

            total += len(records)
            log.info(
                "  ✓ %d lecturas  |  nivel_freatico: %.2f m → %.2f m  |  "
                "precip_max: %.1f mm",
                len(records),
                df["nivel_freatico_m"].iloc[0],
                df["nivel_freatico_m"].iloc[-1],
                df["precipitacion_mm"].max(),
            )

        log.info("=" * 60)
        log.info("  SEED COMPLETADO: %d lecturas totales insertadas.", total)
        log.info("=" * 60)

    except Exception:
        session.rollback()
        log.exception("Error durante el seed — rollback ejecutado.")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mock Sensor Generator para Acuífero-Data SCZ"
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="No eliminar lecturas existentes antes de insertar (modo append).",
    )
    args = parser.parse_args()
    seed_sensors(clear_existing=not args.no_clear)
