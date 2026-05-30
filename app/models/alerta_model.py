from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func
from app.database import Base


class Alerta(Base):
    __tablename__ = "alertas"

    id                = Column(Integer, primary_key=True, index=True)
    municipio_id      = Column(Integer, ForeignKey("municipios.id"))
    municipio_nombre  = Column(String)
    tipo              = Column(String)      # sequia | sobreextraccion | contaminacion
    descripcion       = Column(String)
    severidad         = Column(String)      # warning | critical
    activa            = Column(Boolean, default=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
