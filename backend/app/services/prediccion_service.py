"""
Predicción Service — Acuífero-Data SCZ
========================================
Reemplaza las predicciones hardcodeadas con un algoritmo real basado
en los datos históricos de los sensores físicos del municipio.

Pipeline por municipio:
  1. Seleccionar el sensor más crítico (mayor score de riesgo)
  2. EWMA(90d) del nivel freático → señal suavizada, libre de ruido diario
  3. Regresión lineal sobre los últimos 180 días de EWMA → pendiente real
  4. Extrapolación al umbral crítico (15% del pico histórico o 1.0 m)
     → días hasta el colapso → meses_criticos
  5. Proyección mensual a 6 meses (% del nivel histórico máximo)
  6. Precipitación histórica: promedio mensual de los últimos 6 meses

Por qué el sensor más crítico y no el promedio:
  Consistente con la filosofía Max-Pooling: la predicción del municipio
  la determina el peor escenario, no la media.

Complejidad: O(S × N) por solicitud, sin entrenamiento, determinista.
  S = número de sensores del municipio (3–5)
  N = número de lecturas (≤ 730)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.dtos.prediccion_dto import PrediccionResponse
from app.repositories.sensor_repository import SensorRepository
from app.services.sensor_service import _calcular_score_sensor

_sensor_repo = SensorRepository()

# El nivel freático es "crítico" cuando cae por debajo del 15% del pico histórico
# o de 1.0 m (el que sea mayor), lo que sea más restrictivo.
_CRITICAL_FRACTION  = 0.15
_CRITICAL_ABSOLUTE  = 1.0

# Si no hay tendencia descendente, reportar N meses de horizonte seguro
_HORIZONTE_ESTABLE  = 60   # 5 años


def _clasificar_tendencia(meses: int, slope: float, nivel_pct: float) -> str:
    """
    Clasifica la tendencia textual según la pendiente y el tiempo al colapso.

    nivel_pct: nivel actual como fracción del pico histórico (0–1).
    """
    if slope >= 0:
        # Nivel subiendo o estable
        return "estable" if nivel_pct >= 0.50 else "estable_riesgo_medio"
    if meses <= 6:
        return "critica_inmediata"
    if meses <= 18:
        return "descendente_severo"
    if meses <= 36:
        return "descendente_leve"
    return "estable"


class PrediccionService:
    def __init__(self, db: Session):
        self.db = db

    # ── Punto de entrada público ──────────────────────────────────────────────

    def get_by_municipio(self, municipio_id: int) -> PrediccionResponse:
        sensores = _sensor_repo.get_by_municipio(self.db, municipio_id)
        if not sensores:
            raise HTTPException(
                status_code=404,
                detail="Sin sensores registrados para este municipio.",
            )

        # Seleccionar el sensor con mayor score de riesgo
        worst_readings = None
        worst_score    = -1.0

        for sensor in sensores:
            readings = _sensor_repo.get_readings(self.db, sensor.id, days=730)
            if not readings:
                continue
            score, _ = _calcular_score_sensor(readings)
            if score > worst_score:
                worst_score    = score
                worst_readings = readings

        if not worst_readings:
            raise HTTPException(
                status_code=404,
                detail="Sin lecturas de sensores para este municipio.",
            )

        return self._calcular_prediccion(worst_readings)

    # ── Algoritmo de predicción ───────────────────────────────────────────────

    def _calcular_prediccion(self, readings: list) -> PrediccionResponse:
        niveles = pd.Series([r.nivel_freatico_m for r in readings], dtype=float)
        precips = pd.Series([r.precipitacion_mm  for r in readings], dtype=float)

        n = len(niveles)

        # ── 1. EWMA(90d) para suavizar ──────────────────────────────────────
        ewma = niveles.ewm(span=90, adjust=False).mean()

        # ── 2. Regresión lineal en dos ventanas ─────────────────────────────
        # Ventana estructural (365d): captura la tendencia anual real,
        # inmune a rebotes estacionales de 1–3 meses.
        # Ventana reciente (90d): captura el momentum actual.
        # Blend 65%/35%: la tendencia estructural domina la proyección
        # pero el momentum reciente ajusta el corto plazo.
        window_struct  = min(365, n)
        window_recent  = min(90,  n)

        def _slope(series: np.ndarray) -> float:
            idx = np.arange(len(series), dtype=float)
            return float(np.polyfit(idx, series, 1)[0])

        slope_struct = _slope(ewma.iloc[-window_struct:].values)
        slope_recent = _slope(ewma.iloc[-window_recent:].values)
        # Blend: usa la pendiente estructural para meses_criticos/tendencia
        # y el blend para la proyección a 6 meses
        slope_blend  = 0.65 * slope_struct + 0.35 * slope_recent

        current_ewma = float(ewma.iloc[-1])
        hist_max     = float(niveles.max())
        hist_min     = float(niveles.min())

        # ── 3. Umbral crítico ───────────────────────────────────────────────
        critical = max(_CRITICAL_ABSOLUTE, hist_max * _CRITICAL_FRACTION)

        # ── 4. Días hasta el umbral → meses_criticos ────────────────────────
        if current_ewma <= critical:
            # Ya está en zona crítica
            days_to_critical = 0
        elif slope_struct >= 0:
            days_to_critical = _HORIZONTE_ESTABLE * 30
        else:
            # current + slope_struct * t = critical
            days_to_critical = max(0, int((critical - current_ewma) / slope_struct))

        meses_criticos = max(0, min(_HORIZONTE_ESTABLE, days_to_critical // 30))

        # ── 5. Tendencia textual ─────────────────────────────────────────────
        nivel_pct = current_ewma / hist_max if hist_max > 0 else 0.0
        tendencia = _clasificar_tendencia(meses_criticos, slope_struct, nivel_pct)

        # ── 6. Proyección mensual a 6 meses (en % del pico histórico) ───────
        # Usa slope_blend para capturar tanto la tendencia estructural
        # como el momentum reciente (rebote estacional o empeoramiento agudo)
        proyeccion: list[float] = []
        for month in range(1, 7):
            days      = month * 30
            projected = current_ewma + slope_blend * days
            projected = float(np.clip(projected, hist_min * 0.5, hist_max))
            pct       = round((projected / hist_max) * 100, 1) if hist_max > 0 else 0.0
            proyeccion.append(pct)

        # ── 7. Precipitación histórica: últimos 6 meses (promedio mensual) ──
        readings_per_month = max(1, n // 6)
        precip_historica: list[float] = []
        for i in range(6, 0, -1):
            start  = n - i * readings_per_month
            end    = n - (i - 1) * readings_per_month
            bucket = precips.iloc[max(0, start):end]
            precip_historica.append(round(float(bucket.mean()), 1) if len(bucket) else 0.0)

        return PrediccionResponse(
            tendencia              = tendencia,
            meses_criticos         = meses_criticos,
            proyeccion             = proyeccion,
            precipitacion_historica= precip_historica,
        )
