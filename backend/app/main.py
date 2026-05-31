from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pytz import utc

from app.config import settings
from app.database import Base, engine
from app.controllers import (
    municipio_controller,
    prediccion_controller,
    alerta_controller,
    gemini_controller,
    reading_controller,
    sensor_controller,
)
from app.services import scheduler_service

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida de la aplicación:
      Arranque  — precalcula tendencias EWMA y lanza el scheduler de sensores
      Apagado   — detiene el scheduler limpiamente
    """
    # Precalcular tendencias EWMA para todos los sensores activos
    scheduler_service.precompute_trends()

    # Scheduler en background (hilo propio, no bloquea el event loop)
    scheduler = BackgroundScheduler(timezone=utc)
    # Job 1: genera lecturas nuevas en todos los sensores
    scheduler.add_job(
        scheduler_service.tick,
        trigger="interval",
        minutes=settings.sensor_interval_minutes,
        id="sensor_tick",
        max_instances=1,
        replace_existing=True,
    )
    # Job 2: recalcula score_riesgo y nivel_riesgo de los municipios
    scheduler.add_job(
        scheduler_service.sync_scores,
        trigger="interval",
        minutes=settings.score_sync_minutes,
        id="score_sync",
        max_instances=1,
        replace_existing=True,
    )
    scheduler.start()
    scheduler_service.set_activo(True, settings.sensor_interval_minutes, settings.score_sync_minutes)

    # Ticks iniciales: lecturas frescas + scores actualizados al arrancar
    scheduler_service.tick()
    scheduler_service.sync_scores()

    yield

    scheduler.shutdown(wait=False)
    scheduler_service.set_activo(False)


app = FastAPI(
    title="Acuífero-Data SCZ API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(municipio_controller.router)
app.include_router(prediccion_controller.router)
app.include_router(alerta_controller.router)
app.include_router(gemini_controller.router)
app.include_router(reading_controller.router)
app.include_router(sensor_controller.router)


@app.get("/")
def root():
    return {"status": "online", "proyecto": "Acuífero-Data SCZ"}
