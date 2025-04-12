from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

from .database.database import engine, Base
from .models import models
from .routers import auth, workspace, chat, upload, reports

# Load environment variables
load_dotenv()

# Create database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Financial Research Assistant API",
    description="API for AI-powered financial research assistant",
    version="0.1.0",
)

# Configure CORS
origins = [
    "http://localhost:5173",  # React dev server
    "http://localhost:8000",  # FastAPI server
    "*",                      # Allow all origins (remove in production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory if it doesn't exist
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static file directory for uploads
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(workspace.router)
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(reports.router)

@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to the Financial Research Assistant API"}

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"} 