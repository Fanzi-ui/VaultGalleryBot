from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from web.schemas import ModelResponse, ModelCreate, ModelUpdate
from web.dependencies import get_db
from services import model_service, storage_service
from models.model_entity import Model # Only needed for type hints

from web.auth import require_api_key # Import the new API key dependency

router = APIRouter(prefix="/api/models", tags=["models"], dependencies=[Depends(require_api_key)])


@router.post("/", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
def create_model_endpoint(model_create: ModelCreate, db: Session = Depends(get_db)):
    # Check if a model with the same normalized name already exists
    normalized_name = model_service._normalize_model_query(model_create.name)
    existing_model = db.query(Model).filter(Model.normalized_name == normalized_name).first()
    if existing_model:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model with this name already exists.")

    created_model = model_service.create_model(db, model_create)
    return created_model

@router.get("/", response_model=List[ModelResponse])
def get_all_models_endpoint(db: Session = Depends(get_db)):
    models = model_service.get_all_models(db)
    return models

@router.get("/{model_id}", response_model=ModelResponse)
def get_model_endpoint(model_id: int, db: Session = Depends(get_db)):
    model = model_service.get_model_by_id_with_session(db, model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return model

@router.put("/{model_id}", response_model=ModelResponse)
def update_model_endpoint(model_id: int, model_update: ModelUpdate, db: Session = Depends(get_db)):
    updated_model = model_service.update_model(db, model_id, model_update)
    if not updated_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return updated_model

@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model_endpoint(model_id: int, db: Session = Depends(get_db)):
    model_to_delete = model_service.get_model_by_id_with_session(db, model_id)
    if not model_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    
    model_name = model_to_delete.name

    deleted, media_records = model_service.delete_model_by_id(db, model_id)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete model")

    storage_service.delete_media_files(media_records)
    storage_service.delete_model_directory(model_name)
    
    return {"message": "Model and associated media deleted successfully"}