from sqlalchemy import Column, Integer, String
from .database import Base


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    normalized_name = Column(String, unique=True, nullable=False, index=True)
    popularity = Column(Integer, nullable=True)
    versatility = Column(Integer, nullable=True)
    longevity = Column(Integer, nullable=True)
    industry_impact = Column(Integer, nullable=True)
    fan_appeal = Column(Integer, nullable=True)
