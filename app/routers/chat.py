from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import json
from pydantic import BaseModel

from ..database.database import get_db, SessionLocal
from ..models.models import User, Chat, Message, Workspace
from ..schemas.schemas import (
    ChatCreate, ChatResponse, MessageCreate, MessageResponse, 
    WebSocketMessage, QueryResponse, TableModel, GraphModel
)
from ..auth.auth import get_current_active_user
import asyncio

from src.main import process_query
from src.visualization_extractor import extract_visualizations


router = APIRouter(
    prefix="/chats",
    tags=["Chats"],
    responses={404: {"description": "Not found"}},
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}  # chat_id -> list of WebSocket connections

    async def connect(self, websocket: WebSocket, chat_id: int, user_id: int):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append({"websocket": websocket, "user_id": user_id})

    def disconnect(self, websocket: WebSocket, chat_id: int):
        if chat_id in self.active_connections:
            self.active_connections[chat_id] = [
                conn for conn in self.active_connections[chat_id] 
                if conn["websocket"] != websocket
            ]
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]

    async def broadcast(self, message: dict, chat_id: int):
        if chat_id in self.active_connections:
            for connection in self.active_connections[chat_id]:
                await connection["websocket"].send_text(json.dumps(message))

manager = ConnectionManager()

@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
def create_chat(
    chat: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new chat."""
    # If workspace_id is provided, check if user is a member of the workspace
    if chat.workspace_id:
        workspace = db.query(Workspace).filter(Workspace.id == chat.workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        if current_user not in workspace.members:
            raise HTTPException(status_code=403, detail="Not authorized to create chat in this workspace")
    
    db_chat = Chat(
        title=chat.title,
        user_id=current_user.id,
        workspace_id=chat.workspace_id
    )
    
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    
    return db_chat

@router.get("/", response_model=List[ChatResponse])
def get_chats(
    skip: int = 0,
    limit: int = 100,
    workspace_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all chats for the current user, optionally filtered by workspace."""
    query = db.query(Chat).filter(Chat.user_id == current_user.id)
    
    if workspace_id:
        # Check if user is a member of the workspace
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        if current_user not in workspace.members:
            raise HTTPException(status_code=403, detail="Not authorized to access this workspace")
        
        query = query.filter(Chat.workspace_id == workspace_id)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{chat_id}", response_model=ChatResponse)
def get_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific chat by ID."""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Check if the user owns the chat or is a member of the workspace
    if chat.user_id != current_user.id:
        if chat.workspace_id:
            workspace = db.query(Workspace).filter(Workspace.id == chat.workspace_id).first()
            if not workspace or current_user not in workspace.members:
                raise HTTPException(status_code=403, detail="Not authorized to access this chat")
        else:
            raise HTTPException(status_code=403, detail="Not authorized to access this chat")
    
    return chat

@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a chat."""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Only the chat owner can delete it
    if chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this chat")
    
    db.delete(chat)
    db.commit()
    
    return None

@router.post("/{chat_id}/messages", response_model=MessageResponse)
def create_message(
    chat_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new message in a chat."""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Check if the user has access to the chat
    if chat.user_id != current_user.id:
        if chat.workspace_id:
            workspace = db.query(Workspace).filter(Workspace.id == chat.workspace_id).first()
            if not workspace or current_user not in workspace.members:
                raise HTTPException(status_code=403, detail="Not authorized to post in this chat")
        else:
            raise HTTPException(status_code=403, detail="Not authorized to post in this chat")
    
    db_message = Message(
        content=message.content,
        is_from_user=message.is_from_user,
        chat_id=chat_id,
        user_id=current_user.id
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message

@router.get("/{chat_id}/messages", response_model=List[MessageResponse])
def get_messages(
    chat_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all messages in a chat."""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Check if the user has access to the chat
    if chat.user_id != current_user.id:
        if chat.workspace_id:
            workspace = db.query(Workspace).filter(Workspace.id == chat.workspace_id).first()
            if not workspace or current_user not in workspace.members:
                raise HTTPException(status_code=403, detail="Not authorized to view this chat")
        else:
            raise HTTPException(status_code=403, detail="Not authorized to view this chat")
    
    return db.query(Message).filter(Message.chat_id == chat_id).offset(skip).limit(limit).all()

@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int, token: str, session_id: str = None, workspace_id: int = None):
    """WebSocket endpoint for real-time chat messages."""
    try:
        # Authenticate user from token
        db = SessionLocal()
        try:
            from ..auth.auth import get_current_user
            current_user = await get_current_user(token=token, db=db)
            
            # Check if user has access to the chat
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if not chat:
                await websocket.close(code=1008, reason="Chat not found")
                return
                
            # If workspace_id is provided, verify it matches the chat's workspace
            if workspace_id and chat.workspace_id and int(workspace_id) != chat.workspace_id:
                await websocket.close(code=1008, reason="Workspace ID mismatch")
                return
                
            if chat.user_id != current_user.id:
                if chat.workspace_id:
                    workspace = db.query(Workspace).filter(Workspace.id == chat.workspace_id).first()
                    if not workspace or current_user not in workspace.members:
                        await websocket.close(code=1008, reason="Not authorized to access this chat")
                        return
                else:
                    await websocket.close(code=1008, reason="Not authorized to access this chat")
                    return
            
            client_id = session_id or current_user.id
            await manager.connect(websocket, chat_id, client_id)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)

                    print(f"Received data: {message_data}")
                    
                    # Extract message content from received data
                    content = message_data.get("content", "")
                    if not content:
                        await websocket.send_text(json.dumps({
                            "error": "Message content is required"
                        }))
                        continue
                    
                    # Extract visualization options if provided
                    visualization_options = message_data.get("visualization_options", {})
                    include_tables = visualization_options.get("include_tables", True)
                    include_graphs = visualization_options.get("include_graphs", True)
                    max_tables = visualization_options.get("max_tables", 5)
                    max_graphs = visualization_options.get("max_graphs", 3)
                    
                    # Create a new message in the database
                    db_message = Message(
                        content=content,
                        is_from_user=True,
                        chat_id=chat_id,
                        user_id=current_user.id
                    )
                    
                    db.add(db_message)
                    db.commit()
                    db.refresh(db_message)
                    
                    # Include session_id in the response if it was provided
                    message_response = {
                        "type": "message",
                        "message_type": "user",
                        "data": {
                            "id": db_message.id,
                            "uuid": str(db_message.id),
                            "user": current_user.username or "User",
                            "format": "txt",
                            "content": db_message.content,
                            "is_from_user": db_message.is_from_user,
                            "user_id": db_message.user_id,
                            "chat_id": db_message.chat_id,
                            "created_at": db_message.created_at.isoformat()
                        }
                    }
                    
                    if session_id:
                        message_response["session_id"] = session_id
                        
                    if workspace_id:
                        message_response["workspace_id"] = workspace_id
                    
                    # Broadcast the message to all connected clients
                    await manager.broadcast(message_response, chat_id)

                    # Process the query with the AI
                    ai_response_obj = process_query(db_message.content, user_id=str(current_user.id))
                    
                    # Extract the text response
                    ai_response_text = ai_response_obj.get("response", "Sorry, I couldn't process your request.")
                    
                    # Extract or generate visualizations
                    tables = ai_response_obj.get("tables", [])
                    graphs = ai_response_obj.get("graphs", [])
                    
                    # If tables and graphs are empty, and we should include them, extract them from the text
                    if (include_tables or include_graphs) and (not tables or not graphs):
                        visualizations = extract_visualizations(
                            ai_response_text, 
                            db_message.content,
                            max_tables=max_tables,
                            max_graphs=max_graphs
                        )
                        
                        if include_tables:
                            tables = visualizations.get("tables", [])
                            
                        if include_graphs:
                            graphs = visualizations.get("graphs", [])

                    # Create AI response message in the database
                    ai_message = Message(
                        content=ai_response_text,
                        is_from_user=False,
                        chat_id=chat_id,
                        user_id=current_user.id  # AI response is still associated with the user
                    )
                    
                    db.add(ai_message)
                    db.commit()
                    db.refresh(ai_message)
                    
                    # Prepare AI response with session and workspace IDs if provided
                    ai_response_data = {
                        "type": "message",
                        "message_type": "bot",
                        "data": {
                            "id": ai_message.id,
                            "uuid": str(ai_message.id),
                            "user": "AI Assistant",
                            "format": "md", # Change to markdown format for better rendering
                            "content": ai_message.content,
                            "is_from_user": ai_message.is_from_user,
                            "user_id": ai_message.user_id,
                            "chat_id": ai_message.chat_id,
                            "created_at": ai_message.created_at.isoformat(),
                            "visualizations": {
                                "graphs": graphs,
                                "tables": tables
                            }
                        }
                    }
                    
                    if session_id:
                        ai_response_data["session_id"] = session_id
                        
                    if workspace_id:
                        ai_response_data["workspace_id"] = workspace_id
                    
                    # Broadcast AI response
                    await manager.broadcast(ai_response_data, chat_id)
                    
            except WebSocketDisconnect:
                manager.disconnect(websocket, chat_id)
                
        finally:
            db.close()
            
    except Exception as e:
        await websocket.close(code=1008, reason=str(e)) 

# New model for query requests
class QueryRequest(BaseModel):
    query: str
    
@router.post("/query", response_model=QueryResponse)
async def process_chat_query(
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Process a direct query and return response with visualizations"""
    
    # Process the query
    result = process_query(query_request.query, user_id=str(current_user.id))
    
    # Return the structured response
    return QueryResponse(
        status=result.get("status", "success"),
        query=result.get("query", query_request.query),
        response=result.get("response", ""),
        metadata=result.get("metadata", {}),
        graphs=result.get("graphs", []),
        tables=result.get("tables", [])
    ) 