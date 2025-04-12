from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database.database import get_db
from ..models.models import User, Report
from ..schemas.schemas import ReportCreate, ReportResponse, ReportUpdate
from ..auth.auth import get_current_active_user

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new report."""
    db_report = Report(
        title=report.title,
        description=report.description,
        content=report.content,
        report_type=report.report_type,
        status=report.status,
        pages=report.pages,
        user_id=current_user.id
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return db_report

@router.get("/", response_model=List[ReportResponse])
def get_reports(
    skip: int = 0,
    limit: int = 100,
    report_type: str = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all reports for the current user, with optional filters."""
    query = db.query(Report).filter(Report.user_id == current_user.id)
    
    # Apply filters if provided
    if report_type:
        query = query.filter(Report.report_type == report_type)
    if status:
        query = query.filter(Report.status == status)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific report by ID."""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check if the user owns the report
    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this report")
    
    return report

@router.put("/{report_id}", response_model=ReportResponse)
def update_report(
    report_id: int,
    report_data: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check if the user owns the report
    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this report")
    
    # Update fields if provided
    for key, value in report_data.dict(exclude_unset=True).items():
        setattr(report, key, value)
    
    db.commit()
    db.refresh(report)
    
    return report

@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check if the user owns the report
    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this report")
    
    db.delete(report)
    db.commit()
    
    return None 