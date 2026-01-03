from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from .database import Base


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    file_path = Column(String, nullable=False)
    media_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # NEW: track when media was last sent
    last_sent_at = Column(DateTime, nullable=True)
