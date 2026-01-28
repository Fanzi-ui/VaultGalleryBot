from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import subprocess
import tempfile

from web.schemas import MediaResponse, ModelCreate
from web.dependencies import get_db
from services import model_service, storage_service
from models.model_entity import Model

from web.auth import require_api_key # Import the new API key dependency

router = APIRouter(prefix="/api/media", tags=["media"], dependencies=[Depends(require_api_key)])
MAX_VIDEO_DURATION_SECONDS = 120


def media_path_to_url(file_path: str) -> str:
    if not file_path:
        return ""

    path = file_path.replace("\\\\", "/")

    if "/media/" in path:
        return path[path.index("/media/") :]

    if path.startswith("media/"):
        return "/" + path

    return ""

def _get_video_duration_seconds(file_bytes: bytes, suffix: str) -> float:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as temp_file:
        temp_file.write(file_bytes)
        temp_file.flush()
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    temp_file.name,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Video validation unavailable (ffprobe not installed).",
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not read video metadata for one of the files.",
            ) from exc

    try:
        return float(result.stdout.strip())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video metadata for one of the files.",
        ) from exc

async def _upload_files_for_model(
    db: Session,
    model_id: int,
    files: List[UploadFile],
) -> List[MediaResponse]:
    if not (1 <= len(files) <= 50):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bulk upload supports 1 to 50 files at a time."
        )

    model = model_service.get_model_by_id_with_session(db, model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    uploaded_media_records = []
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided for one of the files.")

        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            media_type = "image"
        elif file_extension in [".mp4", ".mov", ".webm"]:
            media_type = "video"
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported file type: {file.filename}")
        
        file_content = await file.read()
        if media_type == "video":
            duration = _get_video_duration_seconds(file_content, file_extension)
            if duration > MAX_VIDEO_DURATION_SECONDS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Video exceeds 2 minute limit."
                )
        
        try:
            media_record = await storage_service.save_uploaded_media(db, model_id, file_content, file.filename, media_type)
            uploaded_media_records.append(media_record)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload media {file.filename}: {e}")

    return uploaded_media_records

@router.post("/upload", response_model=List[MediaResponse], status_code=status.HTTP_201_CREATED)
async def upload_media(
    files: List[UploadFile] = File(...),
    model_id: Optional[int] = Form(None),
    model_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    resolved_model_id = model_id
    if resolved_model_id is None:
        name = (model_name or "").strip()
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide a model ID or a model name."
            )

        normalized_name = model_service._normalize_model_query(name)
        existing_model = (
            db.query(Model)
            .filter(Model.normalized_name == normalized_name)
            .first()
        )
        if existing_model:
            resolved_model_id = existing_model.id
        else:
            created_model = model_service.create_model(db, ModelCreate(name=name))
            resolved_model_id = created_model.id

    return await _upload_files_for_model(db, resolved_model_id, files)

@router.post("/upload/{model_id}", response_model=List[MediaResponse], status_code=status.HTTP_201_CREATED)
async def upload_media_for_model(
    model_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    return await _upload_files_for_model(db, model_id, files)

@router.get("/{media_id}", response_model=MediaResponse)
def get_media_item_by_id(media_id: int, db: Session = Depends(get_db)):
    media_item = model_service.get_media_by_id_with_session(db, media_id)
    if not media_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
    return media_item

@router.get("/model/{model_id}", response_model=List[MediaResponse])
def get_all_media_for_model_endpoint(model_id: int, db: Session = Depends(get_db)):
    model = model_service.get_model_by_id_with_session(db, model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    
    media_items = model_service.get_all_media_for_model(db, model_id)
    return media_items

@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media_item(media_id: int, db: Session = Depends(get_db)):
    media_item = model_service.get_media_by_id_with_session(db, media_id)
    if not media_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
    
    # Delete file from storage
    storage_service.delete_media_files([media_item]) # Pass as list as expected by function
    
    # Delete record from database
    deleted = model_service.delete_media_by_id(db, media_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete media record")
    
    return {"message": "Media deleted successfully"}
