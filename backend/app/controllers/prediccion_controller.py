from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dtos.prediccion_dto import PrediccionResponse
from app.services.prediccion_service import PrediccionService

router = APIRouter(prefix="/prediccion", tags=["predicciones"])


@router.get("/{municipio_id}", response_model=PrediccionResponse)
def get_prediccion(municipio_id: int, db: Session = Depends(get_db)):
    return PrediccionService(db).get_by_municipio(municipio_id)
