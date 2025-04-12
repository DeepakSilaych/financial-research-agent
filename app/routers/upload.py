from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path
from datetime import datetime

from ..database.database import get_db
from ..models.models import User, Upload
from ..schemas.schemas import UploadResponse
from ..auth.auth import get_current_active_user

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get upload directory from environment variable or use default
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")

router = APIRouter(
    prefix="/uploads",
    tags=["Uploads"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a file."""
    # Create user upload directory if it doesn't exist
    user_upload_dir = Path(UPLOAD_DIR) / f"user_{current_user.id}"
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{timestamp}_{file.filename}"
    
    # Save file to disk
    file_path = os.path.join(user_upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Create database record
    db_upload = Upload(
        filename=file.filename,
        file_path=str(Path(f"user_{current_user.id}") / unique_filename),
        file_size=file_size,
        file_type=file.content_type,
        description=description,
        user_id=current_user.id
    )
    
    db.add(db_upload)
    db.commit()
    db.refresh(db_upload)
    
    return db_upload

@router.get("/", response_model=List[UploadResponse])
def get_uploads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all uploads for the current user."""
    return db.query(Upload).filter(Upload.user_id == current_user.id).offset(skip).limit(limit).all()

@router.get("/{upload_id}", response_model=UploadResponse)
def get_upload(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific upload by ID."""
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Check if the user owns the upload
    if upload.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this upload")
    
    return upload

@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_upload(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an upload."""
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Check if the user owns the upload
    if upload.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this upload")
    
    # Delete file from disk
    file_path = os.path.join(UPLOAD_DIR, upload.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete database record
    db.delete(upload)
    db.commit()
    
    return None

@router.get("/download/{upload_id}")
def download_upload(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get download URL for an upload."""
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Check if the user owns the upload
    if upload.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this upload")
    
    # In a real app, this would generate a signed URL or serve the file
    # For simplicity, we just return the path
    return {"download_url": f"/uploads/{upload.file_path}", "filename": upload.filename} 