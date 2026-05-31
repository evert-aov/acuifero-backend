"""
Multi-Sensor Seed — Acuífero-Data SCZ
=======================================
Genera 3-5 sensores físicos por municipio, cada uno con su propia
variación del comportamiento base. Inserta lecturas diarias (2 años)
por sensor en la tabla `readings` con `sensor_id` poblado.

Por qué múltiples sensores:
  - Un sensor en zona urbana puede estar al límite mientras uno en
    zona reserva está estable → el promedio escondería la crisis.
  - El backend usa Max-Pooling para detectar el peor escenario.

Uso:
  cd acuifero-data-backend/backend
  python -m app.seeds.seed_multi_sensor              # borra sensores/lecturas previas
  python -m app.seeds.seed_multi_sensor --no-clear   # modo append
"""

import argparse
import logging
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sqlalchemy import text

from app.database import SessionLocal, engine, Base
from app.models.reading_model  import Reading
from app.models.municipio_model import Municipio
from app.models.sensor_model    import Sensor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)-8s]  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

TWO_YEARS_DAYS = 730
BATCH_SIZE     = 5_000
RNG_SEED       = 2024

# ---------------------------------------------------------------------------
# Configuración de sensores por municipio
# Cada sensor tiene:
#   zona           : tipo de zona (afecta la narrativa)
#   delta_lat/lng  : desplazamiento en grados desde el centroide del municipio
#   offset_nivel   : ajuste en metros del nivel freático base
#   factor_extrac  : multiplicador de la extracción base
#   noise_sigma    : σ adicional de ruido para este sensor (m)
# ---------------------------------------------------------------------------
# fmt: off
SENSOR_CONFIGS: dict[int, list[dict]] = {
    1:  [  # Santa Cruz de la Sierra
        {"zona": "urbano_central", "delta_lat":  0.00, "delta_lng":  0.00, "offset_nivel": -1.5, "factor_extrac": 1.25, "noise_sigma": 0.05},
        {"zona": "periurbano_norte","delta_lat":  0.05, "delta_lng":  0.03, "offset_nivel":  0.5, "factor_extrac": 0.90, "noise_sigma": 0.04},
        {"zona": "agricola_este",  "delta_lat": -0.04, "delta_lng":  0.06, "offset_nivel":  1.0, "factor_extrac": 1.10, "noise_sigma": 0.06},
        {"zona": "reserva_oeste",  "delta_lat":  0.02, "delta_lng": -0.07, "offset_nivel":  2.5, "factor_extrac": 0.60, "noise_sigma": 0.03},
        {"zona": "industrial_sur", "delta_lat": -0.06, "delta_lng": -0.02, "offset_nivel": -2.0, "factor_extrac": 1.45, "noise_sigma": 0.07},
    ],
    2:  [  # Charagua — zona de sobreexplotación
        {"zona": "urbano",         "delta_lat":  0.00, "delta_lng":  0.00, "offset_nivel": -0.8, "factor_extrac": 1.20, "noise_sigma": 0.06},
        {"zona": "agricola_norte", "delta_lat":  0.04, "delta_lng":  0.02, "offset_nivel":  0.3, "factor_extrac": 1.30, "noise_sigma": 0.05},
        {"zona": "ganadero_sur",   "delta_lat": -0.05, "delta_lng":  0.01, "offset_nivel": -1.2, "factor_extrac": 1.50, "noise_sigma": 0.08},
    ],
    3:  [  # Cabezas
        {"zona": "urbano",         "delta_lat":  0.00, "delta_lng":  0.00, "offset_nivel": -0.5, "factor_extrac": 1.15, "noise_sigma": 0.05},
        {"zona": "agricola",       "delta_lat":  0.03, "delta_lng":  0.04, "offset_nivel":  0.8, "factor_extrac": 1.20, "noise_sigma": 0.06},
        {"zona": "periurbano",     "delta_lat": -0.03, "delta_lng": -0.03, "offset_nivel":  0.2, "factor_extrac": 0.85, "noise_sigma": 0.04},
    ],
    4:  [  # San Ignacio de Velasco
        {"zona": "urbano",         "delta_lat":  0.00, "delta_lng":  0.00, "offset_nivel": -0.6, "factor_extrac": 1.10, "noise_sigma": 0.04},
        {"zona": "turismo_norte",  "delta_lat":  0.06, "delta_lng":  0.02, "offset_nivel":  1.5, "factor_extrac": 0.75, "noise_sigma": 0.03},
        {"zona": "agricola",       "delta_lat": -0.04, "delta_lng":  0.05, "offset_nivel":  0.8, "factor_extrac": 1.05, "noise_sigma": 0.05},
        {"zona": "ganadero",       "delta_lat":  0.02, "delta_lng": -0.06, "offset_nivel": -0.9, "factor_extrac": 1.20, "noise_sigma": 0.06},
    ],
    5:  [  # Concepción
        {"zona": "urbano",         "delta_lat":  0.00, "delta_lng":  0.00, "offset_nivel": -0.4, "factor_extrac": 1.08, "noise_sigma": 0.04},
        {"zona": "agricola",       "delta_lat":  0.04, "delta_lng":  0.03, "offset_nivel":  0.7, "factor_extrac": 1.15, "noise_sigma": 0.05},
        {"zona": "bosque",         "delta_lat": -0.03, "delta_lng": -0.04, "offset_nivel":  2.0, "factor_extrac": 0.50, "noise_sigma": 0.03},
    ],
    6:  [  # San José de Chiquitos — sobreexplotación severa
        {"zona": "urbano",         "delta_lat":  0.00, "delta_lng":  0.00, "offset_nivel": -1.0, "factor_extrac": 1.30, "noise_sigma": 0.07},
        {"zona": "minero_norte",   "delta_lat":  0.05, "delta_lng":  0.01, "offset_nivel": -2.5, "factor_extrac": 1.65, "noise_sigma": 0.09},
        {"zona": "agricola",       "delta_lat": -0.03, "delta_lng":  0.04, "offset_nivel":  0.5, "factor_extrac": 1.10, "noise_sigma": 0.05},
        {"zona": "reserva",        "delta_lat":  0.02, "delta_lng": -0.05, "offset_nivel":  1.8, "factor_extrac": 0.55, "noise_sigma": 0.03},
    ],
    7:  [  # Montero
        {"zona": "urbano",         "delta_lat":  0.00, "delta_lng":  0.00, "offset_nivel": -0.8, "factor_extrac": 1.15, "noise_sigma": 0.04},
        {"zona": "industrial",     "delta_lat":  0.03, "delta_lng":  0.02, "offset_nivel": -1.5, "factor_extrac": 1.35, "noise_sigma": 0.06},
        {"zona": "agricola",       "delta_lat": -0.04, "delta_lng":  0.04, "offset_nivel":  1.0, "factor_extrac": 1.10, "noise_sigma": 0.05},
        {"zona": "periurbano",     "delta_lat":  0.02, "delta_lng": -0.04, "offset_nivel":  0.3, "factor_extrac": 0.90, "noise_sigma": 0.04},
    ],
    8:  [  # Warnes
        {"zona": "urbano",         "delta_lat":  0.00, "delta_lng":  0.00, "offset_nivel": -0.5, "factor_extrac": 1.10, "noise_sigma": 0.04},
        {"zona": "industrial",     "delta_lat":  0.04, "delta_lng":  0.02, "offset_nivel": -1.2, "factor_extrac": 1.28, "noise_sigma": 0.06},
        {"zona": "agricola",       "delta_lat": -0.03, "delta_lng":  0.05, "offset_nivel":  0.8, "factor_extrac": 1.05, "noise_sigma": 0.05},
    ],
    9:  [  # Mineros
        {"zona": "urbano",         "delta_lat":  0.00, "delta_lng":  0.00, "offset_nivel": -0.3, "factor_extrac": 1.05, "noise_sigma": 0.04},
        {"zona": "cañero_norte",   "delta_lat":  0.05, "delta_lng":  0.02, "offset_nivel":  1.0, "factor_extrac": 0.95, "noise_sigma": 0.05},
        {"zona": "agricola_sur",   "delta_lat": -0.04, "delta_lng":  0.03, "offset_nivel":  0.8, "factor_extrac": 1.02, "noise_sigma": 0.04},
    ],
    10: [  # Camiri — zona crítica
        {"zona": "urbano",         "delta_lat":  0.00, "delta_lng":  0.00, "offset_nivel": -0.5, "factor_extrac": 1.20, "noise_sigma": 0.07},
        {"zona": "petrolero",      "delta_lat":  0.04, "delta_lng":  0.02, "offset_nivel": -1.8, "factor_extrac": 1.50, "noise_sigma": 0.10},
        {"zona": "ganadero",       "delta_lat": -0.03, "delta_lng": -0.03, "offset_nivel":  0.5, "factor_extrac": 1.00, "noise_sigma": 0.06},
    ],
    11: [  # Portachuelo
        {"zona": "urbano",         "delta_lat":  0.00, "delta_lng":  0.00, "offset_nivel": -0.2, "factor_extrac": 1.05, "noise_sigma": 0.03},
        {"zona": "agricola",       "delta_lat":  0.04, "delta_lng":  0.03, "offset_nivel":  0.9, "factor_extrac": 0.98, "noise_sigma": 0.04},
        {"zona": "cítrico",        "delta_lat": -0.03, "delta_lng":  0.04, "offset_nivel":  1.2, "factor_extrac": 0.90, "noise_sigma": 0.04},
    ],
    12: [  # San Ramón
        {"zona": "urbano",         "delta_lat":  0.00, "delta_lng":  0.00, "offset_nivel": -0.6, "factor_extrac": 1.12, "noise_sigma": 0.05},
        {"zona": "agricola",       "delta_lat":  0.03, "delta_lng":  0.03, "offset_nivel":  0.5, "factor_extrac": 1.05, "noise_sigma": 0.05},
        {"zona": "ganadero",       "delta_lat": -0.04, "delta_lng": -0.02, "offset_nivel": -0.8, "factor_extrac": 1.18, "noise_sigma": 0.06},
    ],
    13: [  # Vallegrande
        {"zona": "urbano",         "delta_lat":  0.00, "delta_lng":  0.00, "offset_nivel": -0.4, "factor_extrac": 1.08, "noise_sigma": 0.04},
        {"zona": "agricola",       "delta_lat":  0.04, "delta_lng":  0.03, "offset_nivel":  0.7, "factor_extrac": 1.05, "noise_sigma": 0.05},
        {"zona": "reserva",        "delta_lat": -0.04, "delta_lng": -0.03, "offset_nivel":  1.5, "factor_extrac": 0.70, "noise_sigma": 0.03},
    ],
    14: [  # Samaipata
        {"zona": "urbano",         "delta_lat":  0.00, "delta_lng":  0.00, "offset_nivel": -0.2, "factor_extrac": 1.05, "noise_sigma": 0.03},
        {"zona": "turismo",        "delta_lat":  0.03, "delta_lng":  0.02, "offset_nivel":  0.8, "factor_extrac": 0.80, "noise_sigma": 0.03},
        {"zona": "agricola",       "delta_lat": -0.03, "delta_lng":  0.04, "offset_nivel":  1.0, "factor_extrac": 0.90, "noise_sigma": 0.04},
    ],
    15: [  # Puerto Suárez
        {"zona": "urbano",         "delta_lat":  0.00, "delta_lng":  0.00, "offset_nivel": -0.5, "factor_extrac": 1.10, "noise_sigma": 0.05},
        {"zona": "portuario",      "delta_lat":  0.04, "delta_lng":  0.02, "offset_nivel": -0.8, "factor_extrac": 1.20, "noise_sigma": 0.06},
        {"zona": "humedal",        "delta_lat": -0.05, "delta_lng": -0.03, "offset_nivel":  3.0, "factor_extrac": 0.40, "noise_sigma": 0.04},
        {"zona": "agricola",       "delta_lat":  0.02, "delta_lng":  0.05, "offset_nivel":  1.2, "factor_extrac": 0.95, "noise_sigma": 0.05},
    ],
}
# fmt: on

# Parámetros base heredados del seed original
MUNICIPIO_BASE: dict[int, dict] = {
    1:  {"base_nivel": 18.0, "nivel_amp": 2.2, "base_humedad": 55, "base_extraccion": 420,  "trend_m_day":  0.000,  "rain_factor": 1.00},
    2:  {"base_nivel":  8.5, "nivel_amp": 1.0, "base_humedad": 38, "base_extraccion": 95,   "trend_m_day": -0.0033, "rain_factor": 0.60},
    3:  {"base_nivel":  9.0, "nivel_amp": 1.1, "base_humedad": 40, "base_extraccion": 88,   "trend_m_day": -0.0030, "rain_factor": 0.65},
    4:  {"base_nivel": 14.0, "nivel_amp": 1.8, "base_humedad": 52, "base_extraccion": 130,  "trend_m_day": -0.0008, "rain_factor": 0.90},
    5:  {"base_nivel": 15.0, "nivel_amp": 1.9, "base_humedad": 54, "base_extraccion": 110,  "trend_m_day": -0.0006, "rain_factor": 0.90},
    6:  {"base_nivel": 12.0, "nivel_amp": 1.4, "base_humedad": 50, "base_extraccion": 140,  "trend_m_day": -0.0042, "rain_factor": 0.85},
    7:  {"base_nivel": 20.0, "nivel_amp": 2.5, "base_humedad": 60, "base_extraccion": 310,  "trend_m_day": -0.0008, "rain_factor": 1.10},
    8:  {"base_nivel": 19.5, "nivel_amp": 2.3, "base_humedad": 58, "base_extraccion": 265,  "trend_m_day": -0.0007, "rain_factor": 1.05},
    9:  {"base_nivel": 22.0, "nivel_amp": 2.7, "base_humedad": 62, "base_extraccion": 230,  "trend_m_day":  0.0000, "rain_factor": 1.15},
    10: {"base_nivel":  7.0, "nivel_amp": 0.8, "base_humedad": 32, "base_extraccion": 145,  "trend_m_day": -0.0060, "rain_factor": 0.50},
    11: {"base_nivel": 21.0, "nivel_amp": 2.4, "base_humedad": 61, "base_extraccion": 135,  "trend_m_day":  0.0000, "rain_factor": 1.10},
    12: {"base_nivel": 13.5, "nivel_amp": 1.6, "base_humedad": 51, "base_extraccion": 56,   "trend_m_day": -0.0008, "rain_factor": 0.88},
    13: {"base_nivel": 16.0, "nivel_amp": 1.7, "base_humedad": 48, "base_extraccion": 95,   "trend_m_day": -0.0007, "rain_factor": 0.80},
    14: {"base_nivel": 17.0, "nivel_amp": 1.8, "base_humedad": 50, "base_extraccion": 42,   "trend_m_day":  0.0000, "rain_factor": 0.85},
    15: {"base_nivel": 25.0, "nivel_amp": 3.0, "base_humedad": 70, "base_extraccion": 72,   "trend_m_day":  0.0000, "rain_factor": 1.30},
}


# ---------------------------------------------------------------------------
# Señales auxiliares (copiadas del seed original)
# ---------------------------------------------------------------------------

def _seasonal_phase(doy: np.ndarray) -> np.ndarray:
    return 2 * np.pi * (doy - 15.0) / 365.0


def _inject_extreme_events(
    precipitacion: np.ndarray, n_days: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    n_events = int(rng.integers(9, 15))
    starts   = rng.integers(0, n_days - 4, size=n_events)
    mask     = np.zeros(n_days, dtype=bool)
    for s in starts:
        length = int(rng.integers(3, 5))
        mask[s : s + length] = True
    precipitacion        = precipitacion.copy()
    precipitacion[mask]  = rng.uniform(80, 160, size=int(mask.sum()))
    return precipitacion, mask


# ---------------------------------------------------------------------------
# Generación de lecturas para UN sensor
# ---------------------------------------------------------------------------

def generate_sensor_readings(
    municipio_id: int,
    sensor_id: int,
    base: dict,
    sensor_cfg: dict,
    date_range: pd.DatetimeIndex,
    rng: np.random.Generator,
) -> pd.DataFrame:
    n    = len(date_range)
    days = np.arange(n, dtype=float)
    doy  = date_range.day_of_year.to_numpy(dtype=float)
    phi  = _seasonal_phase(doy)

    rf         = base["rain_factor"]
    extra_sig  = sensor_cfg["noise_sigma"]
    fac_e      = sensor_cfg["factor_extrac"]
    off_n      = sensor_cfg["offset_nivel"]

    # --- Precipitación (igual para todos los sensores del mismo municipio)
    precip_base = 30.0 * rf * (1.0 - np.cos(phi)) / 2.0
    noise_mult  = rng.lognormal(mean=0.3, sigma=0.7, size=n)
    precip_raw  = precip_base * noise_mult
    dry_prob    = np.clip(0.55 * np.cos(phi), 0.0, 0.75)
    dry_days    = rng.random(n) < dry_prob
    precip_raw[dry_days] = 0.0
    precip_raw  = np.clip(precip_raw, 0.0, 100.0)
    precipitacion, extreme_mask = _inject_extreme_events(precip_raw, n, rng)

    # --- Humedad
    base_h     = base["base_humedad"]
    hum_season = base_h + 22.0 * (1.0 - np.cos(phi)) / 2.0
    precip_ma7 = pd.Series(precipitacion).rolling(7, min_periods=1).mean().to_numpy()
    hum_boost  = np.clip(precip_ma7 * 0.30, 0.0, 28.0)
    humedad    = hum_season + hum_boost + rng.normal(0.0, 2.0, n)
    humedad[extreme_mask] = rng.uniform(92.0, 100.0, size=int(extreme_mask.sum()))
    humedad    = np.clip(humedad, 10.0, 100.0)

    # --- Extracción (modulada por factor del sensor)
    base_e     = base["base_extraccion"] * fac_e
    ext_season = base_e * (1.0 + 0.28 * np.cos(phi))
    ext_jitter = rng.normal(0.0, base_e * 0.04, n)
    extraccion = np.clip(ext_season + ext_jitter, base_e * 0.45, base_e * 1.85)

    # --- Nivel freático (con offset propio del sensor + ruido extra)
    base_n      = base["base_nivel"] + off_n
    amp_n       = base["nivel_amp"]
    nivel_season= base_n + amp_n * (1.0 - np.cos(phi)) / 2.0
    trend       = base["trend_m_day"] * days

    white = rng.normal(0.0, extra_sig, n)
    ar1   = pd.Series(white).ewm(span=14, adjust=False).mean().to_numpy()

    recharge = pd.Series(precipitacion).rolling(10, min_periods=1).mean().to_numpy()
    nivel    = nivel_season + trend + ar1 + recharge * 0.016
    nivel    = np.clip(nivel, 0.2, 50.0)

    return pd.DataFrame({
        "timestamp":         date_range,
        "municipio_id":      np.int32(municipio_id),
        "sensor_id":         np.int32(sensor_id),
        "precipitacion_mm":  np.round(precipitacion, 2),
        "humedad_suelo_pct": np.round(humedad, 1),
        "extraccion_lps":    np.round(extraccion, 2),
        "nivel_freatico_m":  np.round(nivel, 3),
    })


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def seed_multi_sensor(clear_existing: bool = True) -> None:
    log.info("=" * 60)
    log.info("  Multi-Sensor Seed — Acuífero-Data SCZ")
    log.info("=" * 60)

    Base.metadata.create_all(bind=engine)
    log.info("Tablas verificadas/creadas.")

    end_dt    = datetime.now(tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start_dt  = end_dt - pd.Timedelta(days=TWO_YEARS_DAYS - 1)
    date_range = pd.date_range(start=start_dt, end=end_dt, freq="D", tz="UTC")
    log.info("Rango: %s → %s  (%d días)", start_dt.date(), end_dt.date(), len(date_range))

    rng     = np.random.default_rng(RNG_SEED)
    session = SessionLocal()

    try:
        if clear_existing:
            n_r = session.execute(text("DELETE FROM readings")).rowcount
            session.commit()
            log.info("Lecturas eliminadas: %d", n_r)

            n_s = session.execute(text("DELETE FROM sensores")).rowcount
            session.commit()
            log.info("Sensores eliminados: %d", n_s)

        # Recuperar municipios para obtener lat/lng
        municipios = {m.id: m for m in session.query(Municipio).all()}
        if not municipios:
            log.error("No hay municipios en la BD. Ejecuta primero el seed de municipios.")
            return

        total_lecturas = 0

        for mun_id, sensor_cfgs in SENSOR_CONFIGS.items():
            mun   = municipios.get(mun_id)
            base  = MUNICIPIO_BASE.get(mun_id)
            if mun is None or base is None:
                log.warning("Municipio %d no encontrado, omitiendo.", mun_id)
                continue

            log.info("Municipio %-3d  (%s) — %d sensores", mun_id, mun.nombre, len(sensor_cfgs))

            for idx, cfg in enumerate(sensor_cfgs, start=1):
                sensor = Sensor(
                    municipio_id  = mun_id,
                    nombre        = f"Sensor {idx} — {cfg['zona'].replace('_', ' ').title()}",
                    zona          = cfg["zona"],
                    lat           = round(mun.lat + cfg["delta_lat"], 6),
                    lng           = round(mun.lng + cfg["delta_lng"], 6),
                    offset_nivel  = cfg["offset_nivel"],
                    factor_extrac = cfg["factor_extrac"],
                    activo        = True,
                )
                session.add(sensor)
                session.flush()  # obtener sensor.id

                df      = generate_sensor_readings(mun_id, sensor.id, base, cfg, date_range, rng)
                records = df.to_dict(orient="records")

                for i in range(0, len(records), BATCH_SIZE):
                    session.execute(Reading.__table__.insert(), records[i : i + BATCH_SIZE])
                    session.commit()

                total_lecturas += len(records)
                log.info(
                    "  ✓ sensor_id=%-4d  zona=%-20s  nivel: %.2f→%.2f m  lecturas: %d",
                    sensor.id, cfg["zona"],
                    df["nivel_freatico_m"].iloc[0],
                    df["nivel_freatico_m"].iloc[-1],
                    len(records),
                )

        log.info("=" * 60)
        log.info("  SEED COMPLETADO: %d lecturas totales.", total_lecturas)
        log.info("=" * 60)

    except Exception:
        session.rollback()
        log.exception("Error — rollback ejecutado.")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Sensor Seed — Acuífero-Data SCZ")
    parser.add_argument("--no-clear", action="store_true", help="No borrar datos existentes.")
    args = parser.parse_args()
    seed_multi_sensor(clear_existing=not args.no_clear)
