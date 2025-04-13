from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json

from ..database.database import get_db
from ..models.models import User, Report, Workspace
from ..schemas.schemas import ReportCreate, ReportResponse, ReportUpdate, TableModel, GraphModel
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
    """Create a new report, optionally with visualization data."""
    
    # Check workspace access if a workspace_id is provided
    if report.workspace_id:
        workspace = db.query(Workspace).filter(Workspace.id == report.workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Check if the user has access to the workspace
        if current_user not in workspace.members:
            raise HTTPException(status_code=403, detail="Not authorized to create report in this workspace")
    
    # Extract visualization data
    tables = report.tables if hasattr(report, 'tables') and report.tables else []
    graphs = report.graphs if hasattr(report, 'graphs') and report.graphs else []
    
    # Prepare visualizations JSON
    visualizations = {
        "tables": [table.dict() for table in tables],
        "graphs": [graph.dict() for graph in graphs]
    }
    
    # Create the report record
    db_report = Report(
        title=report.title,
        description=report.description,
        content=report.content,
        report_type=report.report_type,
        status=report.status,
        pages=report.pages,
        user_id=current_user.id,
        workspace_id=report.workspace_id,
        visualizations=json.dumps(visualizations)
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    # Prepare response with visualizations
    response = ReportResponse.from_orm(db_report)
    
    # Add visualization data to response
    try:
        if db_report.visualizations:
            vis_data = json.loads(db_report.visualizations)
            response.tables = [TableModel(**table) for table in vis_data.get("tables", [])]
            response.graphs = [GraphModel(**graph) for graph in vis_data.get("graphs", [])]
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        print(f"Error parsing visualizations: {e}")
    
    return response

@router.get("/", response_model=List[ReportResponse])
def get_reports(
    skip: int = 0,
    limit: int = 100,
    report_type: str = None,
    status: str = None,
    workspace_id: int = None,
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
    if workspace_id:
        # Check if user has access to the workspace
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        if current_user not in workspace.members:
            raise HTTPException(status_code=403, detail="Not authorized to access this workspace")
        
        query = query.filter(Report.workspace_id == workspace_id)
    
    reports = query.offset(skip).limit(limit).all()
    
    # Add visualization data to responses
    result = []
    for report in reports:
        response = ReportResponse.from_orm(report)
        try:
            if report.visualizations:
                vis_data = json.loads(report.visualizations)
                response.tables = [TableModel(**table) for table in vis_data.get("tables", [])]
                response.graphs = [GraphModel(**graph) for graph in vis_data.get("graphs", [])]
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Error parsing visualizations for report {report.id}: {e}")
        
        result.append(response)
    
    return result

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
    
    # Check if the user owns the report or has access to its workspace
    if report.user_id != current_user.id:
        if report.workspace_id:
            workspace = db.query(Workspace).filter(Workspace.id == report.workspace_id).first()
            if not workspace or current_user not in workspace.members:
                raise HTTPException(status_code=403, detail="Not authorized to access this report")
        else:
            raise HTTPException(status_code=403, detail="Not authorized to access this report")
    
    # Prepare response with visualizations
    response = ReportResponse.from_orm(report)
    
    # Add visualization data to response
    try:
        if report.visualizations:
            vis_data = json.loads(report.visualizations)
            response.tables = [TableModel(**table) for table in vis_data.get("tables", [])]
            response.graphs = [GraphModel(**graph) for graph in vis_data.get("graphs", [])]
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        print(f"Error parsing visualizations: {e}")
    
    return response

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

@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate a new report based on selected documents."""
    report_type = data.get("report_type")
    document_ids = data.get("document_ids", [])

    if not report_type:
        raise HTTPException(status_code=400, detail="Report type is required")
    
    if not document_ids:
        raise HTTPException(status_code=400, detail="At least one document must be selected")
    
    # Create a title based on report type
    title = f"{report_type.capitalize()} Report"
    
    # In a real implementation, this would process the documents and generate actual content
    # For this example, we'll create a simple placeholder report
    content = f"This is a generated {report_type} report based on {len(document_ids)} documents."
    
    # Create the report record
    db_report = Report(
        title=title,
        description=f"AI-generated {report_type} report",
        content=content,
        report_type=report_type,
        status="completed",
        pages=1,
        user_id=current_user.id
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return db_report 