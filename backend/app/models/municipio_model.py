from sqlalchemy import Column, Float, Integer, String
from app.database import Base


class Municipio(Base):
    __tablename__ = "municipios"

    id            = Column(Integer, primary_key=True, index=True)
    nombre        = Column(String, nullable=False)
    lat           = Column(Float, nullable=False)
    lng           = Column(Float, nullable=False)
    region        = Column(String)          # chiquitania | chaco | norte_integrado | metropolitana | ...
    poblacion     = Column(Integer)
    nivel_riesgo  = Column(String, default="bajo")   # bajo | medio | alto | critico
    score_riesgo  = Column(Float,  default=0.0)      # 0.0 – 1.0
