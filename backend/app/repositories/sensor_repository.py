from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.sensor_model import Sensor
from app.models.reading_model import Reading


class SensorRepository:
    def get_by_municipio(self, db: Session, municipio_id: int) -> list[Sensor]:
        return (
            db.query(Sensor)
            .filter(Sensor.municipio_id == municipio_id, Sensor.activo == True)
            .all()
        )

    def get_by_id(self, db: Session, sensor_id: int) -> Sensor | None:
        return db.query(Sensor).filter(Sensor.id == sensor_id).first()

    def get_readings(
        self, db: Session, sensor_id: int, days: int = 90
    ) -> list[Reading]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return (
            db.query(Reading)
            .filter(Reading.sensor_id == sensor_id, Reading.timestamp >= cutoff)
            .order_by(Reading.timestamp.asc())
            .all()
        )

    def get_last_reading(self, db: Session, sensor_id: int) -> Reading | None:
        return (
            db.query(Reading)
            .filter(Reading.sensor_id == sensor_id)
            .order_by(Reading.timestamp.desc())
            .first()
        )
