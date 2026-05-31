from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.reading_repository import ReadingRepository
from app.dtos.reading_dto import ReadingResponse

router = APIRouter(prefix="/readings", tags=["readings"])

_repo = ReadingRepository()


@router.get("/{municipio_id}", response_model=list[ReadingResponse])
def get_readings(
    municipio_id: int,
    days: int = Query(default=90, ge=7, le=730, description="Número de días históricos"),
    db: Session = Depends(get_db),
):
    return _repo.get_by_municipio(db, municipio_id, days)


@router.get("/{municipio_id}/last", response_model=ReadingResponse)
def get_last_reading(municipio_id: int, db: Session = Depends(get_db)):
    reading = _repo.get_last(db, municipio_id)
    if reading is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Sin lecturas para este municipio")
    return reading
