from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import json

from ..database.database import get_db, SessionLocal
from ..models.models import User, Chat, Message, Workspace
from ..schemas.schemas import ChatCreate, ChatResponse, MessageCreate, MessageResponse, WebSocketMessage
from ..auth.auth import get_current_active_user

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
async def websocket_endpoint(websocket: WebSocket, chat_id: int, token: str):
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
                
            if chat.user_id != current_user.id:
                if chat.workspace_id:
                    workspace = db.query(Workspace).filter(Workspace.id == chat.workspace_id).first()
                    if not workspace or current_user not in workspace.members:
                        await websocket.close(code=1008, reason="Not authorized to access this chat")
                        return
                else:
                    await websocket.close(code=1008, reason="Not authorized to access this chat")
                    return
            
            # Accept the connection and add it to the connection manager
            await manager.connect(websocket, chat_id, current_user.id)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Create a new message in the database
                    db_message = Message(
                        content=message_data.get("content", ""),
                        is_from_user=True,
                        chat_id=chat_id,
                        user_id=current_user.id
                    )
                    
                    db.add(db_message)
                    db.commit()
                    db.refresh(db_message)
                    
                    # Broadcast the message to all connected clients
                    await manager.broadcast(
                        {
                            "type": "message",
                            "data": {
                                "id": db_message.id,
                                "content": db_message.content,
                                "is_from_user": db_message.is_from_user,
                                "user_id": db_message.user_id,
                                "chat_id": db_message.chat_id,
                                "created_at": db_message.created_at.isoformat()
                            }
                        },
                        chat_id
                    )
                    
                    # Simulate AI response (in a real app, this would call an AI service)
                    ai_response = f"This is a simulated AI response to: {db_message.content}"
                    
                    # Create AI response message
                    ai_message = Message(
                        content=ai_response,
                        is_from_user=False,
                        chat_id=chat_id,
                        user_id=current_user.id  # AI response is still associated with the user
                    )
                    
                    db.add(ai_message)
                    db.commit()
                    db.refresh(ai_message)
                    
                    # Broadcast AI response
                    await manager.broadcast(
                        {
                            "type": "message",
                            "data": {
                                "id": ai_message.id,
                                "content": ai_message.content,
                                "is_from_user": ai_message.is_from_user,
                                "user_id": ai_message.user_id,
                                "chat_id": ai_message.chat_id,
                                "created_at": ai_message.created_at.isoformat()
                            }
                        },
                        chat_id
                    )
                    
            except WebSocketDisconnect:
                manager.disconnect(websocket, chat_id)
                
        finally:
            db.close()
            
    except Exception as e:
        await websocket.close(code=1008, reason=str(e)) 