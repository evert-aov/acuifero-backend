from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.municipio_repository import MunicipioRepository
from app.dtos.municipio_dto import MunicipioResponse


class MunicipioService:
    def __init__(self, db: Session):
        self.repo = MunicipioRepository(db)

    def get_all(self) -> List[MunicipioResponse]:
        municipios = self.repo.get_all()
        return [MunicipioResponse.model_validate(m) for m in municipios]

    def get_by_id(self, municipio_id: int) -> MunicipioResponse:
        municipio = self.repo.get_by_id(municipio_id)
        if not municipio:
            raise HTTPException(status_code=404, detail="Municipio no encontrado")
        return MunicipioResponse.model_validate(municipio)
