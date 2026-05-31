from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.reading_model import Reading


class ReadingRepository:
    def get_by_municipio(
        self, db: Session, municipio_id: int, days: int = 90
    ) -> list[Reading]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return (
            db.query(Reading)
            .filter(Reading.municipio_id == municipio_id, Reading.timestamp >= cutoff)
            .order_by(Reading.timestamp.asc())
            .all()
        )

    def get_last(self, db: Session, municipio_id: int) -> Reading | None:
        return (
            db.query(Reading)
            .filter(Reading.municipio_id == municipio_id)
            .order_by(Reading.timestamp.desc())
            .first()
        )
