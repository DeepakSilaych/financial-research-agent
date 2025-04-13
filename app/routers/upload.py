from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path
from datetime import datetime

from ..database.database import get_db
from ..models.models import User, Upload, Workspace
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
    workspace_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a file."""
    # Handle workspace-specific uploads
    upload_dir_path = Path(UPLOAD_DIR)
    
    if workspace_id:
        # Check if the workspace exists and the user is a member
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
            
        # Check if user is a member of the workspace
        if current_user not in workspace.members:
            raise HTTPException(status_code=403, detail="Not authorized to upload to this workspace")
            
        # Create workspace upload directory
        upload_path = upload_dir_path / f"workspace_{workspace_id}"
        relative_path = Path(f"workspace_{workspace_id}")
    else:
        # Use the user-specific directory as before
        upload_path = upload_dir_path / f"user_{current_user.id}"
        relative_path = Path(f"user_{current_user.id}")
    
    # Create directory if it doesn't exist
    os.makedirs(upload_path, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{timestamp}_{file.filename}"
    
    # Save file to disk
    file_path = os.path.join(upload_path, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Create database record
    db_upload = Upload(
        filename=file.filename,
        file_path=str(relative_path / unique_filename),
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
    workspace_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all uploads for the current user or for a specific workspace."""
    query = db.query(Upload).filter(Upload.user_id == current_user.id)
    
    if workspace_id:
        # Verify workspace exists and user is a member
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
            
        if current_user not in workspace.members:
            raise HTTPException(status_code=403, detail="Not authorized to access this workspace")
            
        # Filter uploads for this workspace by checking the file_path
        workspace_path = f"workspace_{workspace_id}"
        query = query.filter(Upload.file_path.like(f"{workspace_path}/%"))
    else:
        # Filter for user-specific uploads only (not in workspaces)
        user_path = f"user_{current_user.id}"
        query = query.filter(Upload.file_path.like(f"{user_path}/%"))
    
    return query.offset(skip).limit(limit).all()

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
    return {"download_url": f"/files/{upload.file_path}", "filename": upload.filename} 