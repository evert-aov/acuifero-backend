from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.municipio_model import Municipio
from app.dtos.municipio_dto import MunicipioCreate


class MunicipioRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Municipio]:
        return self.db.query(Municipio).all()

    def get_by_id(self, municipio_id: int) -> Optional[Municipio]:
        return self.db.query(Municipio).filter(Municipio.id == municipio_id).first()

    def create(self, data: MunicipioCreate) -> Municipio:
        municipio = Municipio(**data.model_dump())
        self.db.add(municipio)
        self.db.commit()
        self.db.refresh(municipio)
        return municipio

    def delete_all(self) -> None:
        self.db.query(Municipio).delete()
        self.db.commit()
