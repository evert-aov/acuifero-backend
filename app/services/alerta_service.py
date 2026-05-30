from typing import List
from sqlalchemy.orm import Session
from app.repositories.alerta_repository import AlertaRepository
from app.dtos.alerta_dto import AlertaResponse


class AlertaService:
    def __init__(self, db: Session):
        self.repo = AlertaRepository(db)

    def get_active(self) -> List[AlertaResponse]:
        alertas = self.repo.get_active()
        return [AlertaResponse.model_validate(a) for a in alertas]

    def get_by_municipio(self, municipio_id: int) -> List[AlertaResponse]:
        alertas = self.repo.get_by_municipio(municipio_id)
        return [AlertaResponse.model_validate(a) for a in alertas]
