from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Union, Any
from datetime import datetime

# Add the imports for visualization models
from typing import List, Dict, Any, Optional, Union, Literal

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

# Workspace schemas
class WorkspaceBase(BaseModel):
    name: str
    description: Optional[str] = None

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class WorkspaceAddMember(BaseModel):
    user_id: int

class WorkspaceResponse(WorkspaceBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class WorkspaceDetailResponse(WorkspaceResponse):
    members: List[UserResponse]
    
    class Config:
        from_attributes = True

# Chat schemas
class ChatBase(BaseModel):
    title: str
    workspace_id: Optional[int] = None

class ChatCreate(ChatBase):
    pass

class ChatResponse(ChatBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Message schemas
class MessageBase(BaseModel):
    content: str
    is_from_user: bool = True

class MessageCreate(MessageBase):
    chat_id: int

class MessageResponse(MessageBase):
    id: int
    chat_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Visualization schemas
class TableModel(BaseModel):
    title: str
    description: Optional[str] = None
    data: List[List[Any]]  # First row is headers, subsequent rows are data

class GraphDataset(BaseModel):
    label: str
    data: List[Union[int, float, str]]
    borderColor: Optional[str] = None
    backgroundColor: Optional[str] = None

class GraphModel(BaseModel):
    type: Literal["line", "bar", "pie", "scatter", "area", "radar", "mixed"]
    title: str
    description: Optional[str] = None
    labels: List[str]
    datasets: List[GraphDataset]
    xAxis: Optional[str] = None
    yAxis: Optional[str] = None

# Report schemas
class ReportBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: str
    report_type: str
    status: str = "Draft"
    pages: int = 0
    workspace_id: Optional[int] = None

class ReportCreate(ReportBase):
    tables: Optional[List[TableModel]] = []
    graphs: Optional[List[GraphModel]] = []

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    report_type: Optional[str] = None
    status: Optional[str] = None
    pages: Optional[int] = None
    tables: Optional[List[TableModel]] = None
    graphs: Optional[List[GraphModel]] = None

class ReportResponse(ReportBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    tables: List[TableModel] = []
    graphs: List[GraphModel] = []

    class Config:
        from_attributes = True

# Upload schemas
class UploadResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_size: int
    file_type: str
    description: Optional[str] = None
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# WebSocket message schemas
class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Union[str, int, bool, dict]]

class QueryResponse(BaseModel):
    status: str
    query: str
    response: str
    metadata: Optional[Dict[str, Any]] = None
    graphs: List[GraphModel] = []
    tables: List[TableModel] = [] 