from fastapi import APIRouter
from app.dtos.prediccion_dto import PrediccionResponse
from app.services.prediccion_service import PrediccionService

router = APIRouter(prefix="/prediccion", tags=["predicciones"])


@router.get("/{municipio_id}", response_model=PrediccionResponse)
def get_prediccion(municipio_id: int):
    return PrediccionService().get_by_municipio(municipio_id)
