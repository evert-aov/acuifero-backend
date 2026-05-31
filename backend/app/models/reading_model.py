from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer
from app.database import Base


class Reading(Base):
    __tablename__ = "readings"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    timestamp         = Column(DateTime(timezone=True), nullable=False)
    municipio_id      = Column(Integer, ForeignKey("municipios.id"), nullable=False)
    sensor_id         = Column(Integer, ForeignKey("sensores.id"), nullable=True)
    nivel_freatico_m  = Column(Float, nullable=False)
    humedad_suelo_pct = Column(Float, nullable=False)
    extraccion_lps    = Column(Float, nullable=False)
    precipitacion_mm  = Column(Float, nullable=False)

    __table_args__ = (
        Index("ix_readings_municipio_ts", "municipio_id", "timestamp"),
        Index("ix_readings_sensor_ts",    "sensor_id",    "timestamp"),
        Index("ix_readings_timestamp",    "timestamp"),
    )
