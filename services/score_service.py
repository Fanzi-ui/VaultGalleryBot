import os

from models.model_entity import Model
from models.media_entity import Media
from services.avn_service import compute_avn_scores


def _compute_scores(models: list[Model], session) -> dict[str, int]:
    source = os.getenv("CARD_SCORE_SOURCE", "avn").lower()
    
    if source == "avn":
        names = [model.name for model in models]
        return compute_avn_scores(names)
    
    if source == "ml":
        try:
            from services.ml_rating_service import compute_ml_score
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "ML scoring requires torch. Install torch or set CARD_SCORE_SOURCE=avn "
                "or SCORE_ON_START=false to skip ML scoring on startup."
            ) from exc

        ml_scores = {}
        for model in models:
            media_item = session.query(Media).filter_by(model_id=model.id).filter_by(media_type="image").first()
            if media_item and os.path.exists(media_item.file_path):
                try:
                    score = compute_ml_score(media_item.file_path)
                    ml_scores[model.name] = score
                except Exception as e:
                    print(f"Error computing ML score for {model.name} ({media_item.file_path}): {e}")
            else:
                print(f"No image media found for model: {model.name} or file does not exist.")
        return ml_scores
        
    raise RuntimeError(f"Unknown CARD_SCORE_SOURCE: {source}")


def update_model_scores_from_source(session) -> int:
    models = session.query(Model).order_by(Model.name).all()
    scores = _compute_scores(models, session)

    updated = 0
    for model in models:
        score = scores.get(model.name)
        if score is None:
            continue
        model.popularity = score
        model.versatility = score
        model.longevity = score
        model.industry_impact = score
        model.fan_appeal = score
        updated += 1

    session.commit()
    return updated
