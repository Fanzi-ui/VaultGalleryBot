from .database import engine, Base
from . import model_entity
from . import media_entity

Base.metadata.create_all(engine)

print("Database initialized successfully")
