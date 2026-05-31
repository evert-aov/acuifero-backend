from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from app.database import Base


class Sensor(Base):
    __tablename__ = "sensores"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    municipio_id    = Column(Integer, ForeignKey("municipios.id"), nullable=False)
    nombre          = Column(String, nullable=False)
    zona            = Column(String, nullable=False)   # urbano | periurbano | agricola | reserva
    lat             = Column(Float, nullable=False)
    lng             = Column(Float, nullable=False)
    offset_nivel    = Column(Float, default=0.0)       # desviación del nivel base (m)
    factor_extrac   = Column(Float, default=1.0)       # multiplicador de extracción
    activo          = Column(Boolean, default=True)
