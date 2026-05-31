from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dtos.municipio_dto import MunicipioResponse
from app.services.municipio_service import MunicipioService

router = APIRouter(prefix="/municipios", tags=["municipios"])


@router.get("/", response_model=List[MunicipioResponse])
def get_all(db: Session = Depends(get_db)):
    return MunicipioService(db).get_all()


@router.get("/{municipio_id}", response_model=MunicipioResponse)
def get_by_id(municipio_id: int, db: Session = Depends(get_db)):
    return MunicipioService(db).get_by_id(municipio_id)
