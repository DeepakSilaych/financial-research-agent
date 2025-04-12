from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database.database import get_db
from ..models.models import User, Workspace
from ..schemas.schemas import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceDetailResponse,
    WorkspaceUpdate,
    WorkspaceAddMember
)
from ..auth.auth import get_current_active_user

router = APIRouter(
    prefix="/workspaces",
    tags=["Workspaces"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    workspace: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new workspace."""
    db_workspace = Workspace(
        name=workspace.name,
        description=workspace.description,
        owner_id=current_user.id
    )
    
    # Add the creator as a member
    db_workspace.members.append(current_user)
    
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    
    return db_workspace

@router.get("/", response_model=List[WorkspaceResponse])
def get_workspaces(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all workspaces that the user is a member of."""
    return current_user.workspaces[skip : skip + limit]

@router.get("/{workspace_id}", response_model=WorkspaceDetailResponse)
def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific workspace by ID."""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # Check if the user is a member of the workspace
    if current_user not in workspace.members:
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")
        
    return workspace

@router.put("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    workspace_id: int,
    workspace_data: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a workspace."""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # Check if the user is the owner of the workspace
    if workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the workspace owner can update it")
        
    # Update fields if provided
    if workspace_data.name is not None:
        workspace.name = workspace_data.name
    if workspace_data.description is not None:
        workspace.description = workspace_data.description
        
    db.commit()
    db.refresh(workspace)
    
    return workspace

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a workspace."""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # Check if the user is the owner of the workspace
    if workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the workspace owner can delete it")
        
    db.delete(workspace)
    db.commit()
    
    return None

@router.post("/{workspace_id}/members", response_model=WorkspaceDetailResponse)
def add_member_to_workspace(
    workspace_id: int,
    member_data: WorkspaceAddMember,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a member to a workspace."""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # Check if the user is the owner of the workspace
    if workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the workspace owner can add members")
        
    # Get the user to add
    user_to_add = db.query(User).filter(User.id == member_data.user_id).first()
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Check if the user is already a member
    if user_to_add in workspace.members:
        raise HTTPException(status_code=400, detail="User is already a member of this workspace")
        
    # Add the user to the workspace
    workspace.members.append(user_to_add)
    db.commit()
    db.refresh(workspace)
    
    return workspace

@router.delete("/{workspace_id}/members/{user_id}", response_model=WorkspaceDetailResponse)
def remove_member_from_workspace(
    workspace_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a member from a workspace."""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # Check if the user is the owner of the workspace
    if workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the workspace owner can remove members")
        
    # Cannot remove the owner from the workspace
    if user_id == workspace.owner_id:
        raise HTTPException(status_code=400, detail="Cannot remove the workspace owner")
        
    # Get the user to remove
    user_to_remove = db.query(User).filter(User.id == user_id).first()
    if not user_to_remove:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Check if the user is a member
    if user_to_remove not in workspace.members:
        raise HTTPException(status_code=400, detail="User is not a member of this workspace")
        
    # Remove the user from the workspace
    workspace.members.remove(user_to_remove)
    db.commit()
    db.refresh(workspace)
    
    return workspace 