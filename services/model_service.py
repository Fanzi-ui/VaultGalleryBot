from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
from typing import List, Optional
from datetime import datetime

from web.schemas import ModelCreate, ModelUpdate # Import schemas

logger = logging.getLogger(__name__)


def _normalize_model_query(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").split())

def get_model_by_name(model_name: str) -> Model | None:
    session = SessionLocal()
    try:
        normalized_name = _normalize_model_query(model_name)
        return session.query(Model).filter(Model.normalized_name == normalized_name).first()
    finally:
        session.close()

def create_model(db: Session, model_create: ModelCreate) -> Model:
    normalized_name = _normalize_model_query(model_create.name)
    db_model = Model(
        name=model_create.name,
        normalized_name=normalized_name,
        popularity=model_create.popularity,
        versatility=model_create.versatility,
        longevity=model_create.longevity,
        industry_impact=model_create.industry_impact,
        fan_appeal=model_create.fan_appeal,
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

def get_all_models(db: Session) -> List[Model]:
    return db.query(Model).order_by(Model.name).all()

def get_model_by_id_with_session(db: Session, model_id: int) -> Model | None:
    return db.query(Model).filter(Model.id == model_id).first()

def update_model(db: Session, model_id: int, model_update: ModelUpdate) -> Model | None:
    db_model = db.query(Model).filter(Model.id == model_id).first()
    if not db_model:
        return None
    
    for var, value in model_update.model_dump(exclude_unset=True).items():
        if var == "name":
            setattr(db_model, var, value)
            setattr(db_model, "normalized_name", _normalize_model_query(value))
        else:
            setattr(db_model, var, value)
    
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

def delete_model_by_id(db: Session, model_id: int) -> tuple[bool, list[Media]]:
    try:
        media_to_delete = db.query(Media).filter(Media.model_id == model_id).all()
        db.query(Media).filter(Media.model_id == model_id).delete(synchronize_session=False)
        model_deleted = db.query(Model).filter(Model.id == model_id).delete(synchronize_session=False)
        db.commit()
        return model_deleted > 0, media_to_delete
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting model with ID {model_id}: {e}")
        return False, []

def get_media_by_id_with_session(db: Session, media_id: int) -> Media | None:
    return db.query(Media).filter(Media.id == media_id).first()

def get_all_media_for_model(db: Session, model_id: int) -> List[Media]:
    return db.query(Media).filter(Media.model_id == model_id).order_by(Media.created_at.desc()).all()

def delete_media_by_id(db: Session, media_id: int) -> bool:
    try:
        media_deleted = db.query(Media).filter(Media.id == media_id).delete(synchronize_session=False)
        db.commit()
        return media_deleted > 0
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting media with ID {media_id}: {e}")
        return False

def create_media_record(db: Session, model_id: int, file_path: str, media_type: str, rating: Optional[int] = None) -> Media:
    media = Media(
        model_id=model_id,
        file_path=file_path,
        media_type=media_type,
        rating=rating,
        created_at=datetime.utcnow()
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media

def get_models_with_counts():
    """
    Returns a list of (model_name, media_count)
    """
    session = SessionLocal()
    try:
        results = (
            session.query(
                Model.name,
                func.count(Media.id)
            )
            .join(Media, Media.model_id == Model.id)
            .group_by(Model.id)
            .order_by(Model.name.asc())
            .all()
        )
        return results
    finally:
        session.close()

def find_model_matches(user_input: str) -> list[str]:
    normalized_input = _normalize_model_query(user_input)
    if not normalized_input:
        return []

    session = SessionLocal()
    try:
        exact_match = (
            session.query(Model)
            .filter(Model.normalized_name == normalized_input)
            .first()
        )
        if exact_match:
            return [exact_match.name]

        models = session.query(Model).all()
        exact_match = None
        partial_matches = []

        for model in models:
            normalized_model = _normalize_model_query(model.name)
            if normalized_model == normalized_input:
                exact_match = model.name
                break
            if normalized_input in normalized_model:
                partial_matches.append(model.name)

        if exact_match:
            return [exact_match]

        if len(partial_matches) > 1:
            partial_matches.sort()

        return partial_matches
    finally:
        session.close()


def resolve_model_name(user_input: str | None) -> str | None:
    if not user_input:
        return None

    matches = find_model_matches(user_input)
    if len(matches) == 1:
        return matches[0]
    return None
