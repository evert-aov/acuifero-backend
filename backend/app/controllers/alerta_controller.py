from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dtos.alerta_dto import AlertaResponse
from app.services.alerta_service import AlertaService

router = APIRouter(prefix="/alertas", tags=["alertas"])


@router.get("/", response_model=List[AlertaResponse])
def get_active(db: Session = Depends(get_db)):
    return AlertaService(db).get_active()


@router.get("/municipio/{municipio_id}", response_model=List[AlertaResponse])
def get_by_municipio(municipio_id: int, db: Session = Depends(get_db)):
    return AlertaService(db).get_by_municipio(municipio_id)
