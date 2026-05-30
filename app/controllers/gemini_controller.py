from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dtos.prediccion_dto import GeminiResumenRequest, GeminiResumenResponse
from app.services.gemini_service import GeminiService

router = APIRouter(prefix="/gemini", tags=["gemini"])


@router.post("/resumen", response_model=GeminiResumenResponse)
def resumen(request: GeminiResumenRequest, db: Session = Depends(get_db)):
    return GeminiService(db).generar_resumen(request.municipio_id)
