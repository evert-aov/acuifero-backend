from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.dtos.sensor_dto import MunicipioSensorAggregation, SensorResponse
from app.repositories.sensor_repository import SensorRepository
from app.services.sensor_service import SensorService

router = APIRouter(prefix="/sensores", tags=["sensores"])

_sensor_repo = SensorRepository()


@router.get("/{municipio_id}", response_model=list[SensorResponse])
def listar_sensores(municipio_id: int, db: Session = Depends(get_db)):
    """Lista todos los sensores activos de un municipio."""
    return _sensor_repo.get_by_municipio(db, municipio_id)


@router.get("/{municipio_id}/scores", response_model=MunicipioSensorAggregation)
def get_scores(
    municipio_id: int,
    days: int = 90,
    db: Session = Depends(get_db),
):
    """
    Devuelve el score de riesgo individual de cada sensor y el score
    agregado del municipio usando Max-Pooling ponderado.
    """
    return SensorService(db).get_scores_por_municipio(municipio_id, days=days)


@router.get("/{municipio_id}/live")
def get_live(
    municipio_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Lectura en tiempo real simulada de todos los sensores del municipio.
    También dispara en background la actualización del score del municipio en BD.
    """
    svc = SensorService(db)
    background_tasks.add_task(svc.sync_municipio_score, municipio_id)
    return svc.get_live_municipio(municipio_id)


@router.post("/{municipio_id}/sync-score", status_code=204)
def sync_score(municipio_id: int, db: Session = Depends(get_db)):
    """Recalcula el score de un municipio (sin normalización cruzada)."""
    SensorService(db).sync_municipio_score(municipio_id)


@router.post("/sync-all")
def sync_all_scores(days: int = 730, db: Session = Depends(get_db)):
    """
    Recalcula score_riesgo y nivel_riesgo de todos los municipios usando
    EWMA Composite + Max-Pooling + Min-Max Cross-Normalization.
    """
    return SensorService(db).sync_all_scores(days=days)


@router.get("/scheduler/status")
def scheduler_status():
    """Estado del scheduler de monitoreo en tiempo real."""
    from app.services.scheduler_service import get_status
    return get_status()
