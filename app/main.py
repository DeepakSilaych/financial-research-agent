from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

from .database.database import engine, Base
from .models import models
from .routers import auth, workspace, chat, upload, reports
from .db_migrations import run_migrations

# Load environment variables
load_dotenv()

# Run database migrations
run_migrations()

# Create database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

# Create data directories
DATA_DIR = os.getenv("DATA_DIR", "./data")
os.makedirs(os.path.join(DATA_DIR, "embeddings"), exist_ok=True)

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
app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="uploads")

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