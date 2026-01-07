from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media
from sqlalchemy import func


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


def _normalize_model_query(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").split())


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
