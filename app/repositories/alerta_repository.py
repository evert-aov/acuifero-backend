from typing import List
from sqlalchemy.orm import Session
from app.models.alerta_model import Alerta
from app.dtos.alerta_dto import AlertaCreate


class AlertaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active(self) -> List[Alerta]:
        return self.db.query(Alerta).filter(Alerta.activa == True).all()

    def get_by_municipio(self, municipio_id: int) -> List[Alerta]:
        return (
            self.db.query(Alerta)
            .filter(Alerta.municipio_id == municipio_id, Alerta.activa == True)
            .all()
        )

    def create(self, data: AlertaCreate) -> Alerta:
        alerta = Alerta(**data.model_dump())
        self.db.add(alerta)
        self.db.commit()
        self.db.refresh(alerta)
        return alerta

    def delete_all(self) -> None:
        self.db.query(Alerta).delete()
        self.db.commit()
