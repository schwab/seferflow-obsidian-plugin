#!/usr/bin/env python3
"""
SeferFlow Web API - FastAPI Application
Exposed API for PDF audiobook playback with TTS generation, playback control, and MCP interruption.
"""

import secrets
import json
import os
import sys
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
from uuid import uuid4

try:
    import jwt
except ImportError:
    jwt = None

from fastapi import FastAPI, HTTPException, Depends, Header, Request, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.orm import Session as SA_Session
import redis
from redis.exceptions import RedisError
import sqlmodel

# Import seferflow engine (original code)
# Add parent directory to path so we can import seferflow.py
seferflow_dir = Path(__file__).parent.parent.parent  # Go up to seferflow root
sys.path.insert(0, str(seferflow_dir))

from seferflow import (
    PlaybackState,
    generate_speech,
    split_into_chunks,
    save_progress,
    load_progress,
    get_chapter_progress,
    chapter_status,
    file_progress_status,
    directory_progress_status,
    extract_pdf_text,
    preprocess_text,
    trim_silence,
    normalize_audio,
    fmt_time,
    make_progress_bar,
    stream_and_play,
    load_settings,
    save_settings,
    get_chapters,
)

# API Instance
app = FastAPI(
    title="SeferFlow Web API",
    description="PDF Audiobook Playback API with TTS generation, playback control, and MCP interruption",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID Middleware
class RequestIDMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receiver):
        request = scope['http_request']
        request_id = request.get("headers", {}).get("x-request-id", str(uuid4()))
        request["headers"].append(("x-request-id", request_id.encode()))
        await receiver(scope)

# Session Storage (Redis or file-based fallback)
SESSION_STORAGE = os.getenv("SESSION_STORAGE", "file")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    if SESSION_STORAGE == "redis":
        redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_timeout=5,
            retry_on_timeout=True
        )
except RedisError:
    print("⚠ Redis not available, using file-based session storage")
    redis_client = None

# Database Engine
database_engine = sqlmodel.SQLModel
engine = None

try:
    engine = sa_create_engine(
        os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/seferflow"),
        pool_pre_ping=True,
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
    )
    # Try to create tables
    SQLModel.metadata.create_all(bind=engine)
    print("✓ Database connection established")
except Exception as e:
    print(f"⚠ Database not available: {e}")
    print("  API will run without persistence")
    engine = None

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "180"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Create JWT tokens (placeholder)
def create_access_token_sub(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    if not jwt:
        return f"dev-token-{uuid4()}"
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Database Models
class User(SQLModel, table=True):
    """User model"""
    __tablename__ = "users"
    id: Optional[str] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str
    hashed_password: str
    role: str = "listener"  # viewer, listener, admin
    status: str = "active"  # active, suspended, banned
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

class PlaybackSession(SQLModel, table=True):
    """Playback session model"""
    __tablename__ = "sessions"
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str
    pdf_path: str
    chapter: str
    voice: str
    speed: float
    buffer_size: int
    current_position: int = 0
    state: str = "idle"  # idle, playing, paused, stopped
    created_at: datetime = Field(default_factory=datetime.utcnow)
    paused_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None

class ProgressRecord(SQLModel, table=True):
    """Progress tracking model"""
    __tablename__ = "progress"
    id: Optional[str] = Field(default=None, primary_key=True)
    pdf_path: str
    chapter: str
    last_chunk: int = 0
    total_chunks: int = 0
    listen_time: datetime = Field(default_factory=datetime.utcnow)
    progress_percent: float = 0.0

# Request/Response Models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: str
    role: str = "listener"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TTSGenerateRequest(BaseModel):
    text: str
    voice: str = "en-US-AriaNeural"
    speed: float = 1.0

class PlaybackSessionRequest(BaseModel):
    pdf_path: str
    chapter: str
    voice: str = "en-US-AriaNeural"
    speed: float = 1.0
    buffer_size: int = 6

# Helper Functions
def verify_token(token: str) -> Optional[str]:
    """Verify JWT and return user_id"""
    if not jwt:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> Optional[str]:
    """Get current user ID from token"""
    return verify_token(token)

# Auth Endpoints
@app.post("/api/v1/auth/register", status_code=201, response_model=dict)
async def register_user(request: RegisterRequest):
    """Register new user"""
    # Validate password
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not any(c.isupper() for c in request.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")

    # Hash password
    hashed_pw = hashlib.sha256(request.password.encode()).hexdigest()

    # Create user (placeholder)
    user_id = f"user_{int(datetime.utcnow().timestamp())}"
    token = create_access_token_sub(user_id) if jwt else f"dev-token-{uuid4()}"

    return {
        "user_id": user_id,
        "email": request.email,
        "username": request.username,
        "role": request.role,
        "access_token": token,
        "created_at": datetime.utcnow().isoformat(),
        "message": "User registered successfully"
    }

@app.post("/api/v1/auth/login", response_model=Dict[str, Any])
async def login(request: LoginRequest):
    """Login and get JWT token"""
    user_id = f"user_{int(datetime.utcnow().timestamp())}"
    token = create_access_token_sub(user_id) if jwt else f"dev-token-{uuid4()}"

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user_id,
            "email": request.email,
            "role": "listener"
        }
    }

@app.get("/api/v1/auth/me", response_model=Dict[str, Any])
async def get_current_user_info(
    user_id: str = Header(...),
):
    """Get current user info"""
    return {
        "user": {
            "id": user_id,
            "email": f"user@example.com",
            "role": "listener",
            "status": "active"
        },
        "rate_limit_remaining": 60,
        "rate_limit_reset": datetime.utcnow().isoformat()
    }

# PDF Endpoints
@app.get("/api/v1/pdfs/browse")
async def browse_pdfs(
    dir_path: str = Query(...),
    page: int = 0,
    page_size: int = 10,
):
    """Browse PDF library"""
    try:
        items = []
        items_path = Path(dir_path)
        
        if items_path.exists():
            for item in items_path.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    items.append({
                        "type": "directory",
                        "name": item.name,
                        "path": str(item),
                        "status": "partial"
                    })
                elif item.suffix.lower() == ".pdf":
                    items.append({
                        "type": "pdf",
                        "name": item.name,
                        "path": str(item),
                        "status": directory_progress_status(str(item.parent), item.stem)
                    })
        
        # Paginate
        total_pages = (len(items) + page_size - 1) // page_size
        page_items = items[page*page_size:(page+1)*page_size]
        
        return {
            "directory": dir_path,
            "items": page_items,
            "total": len(items),
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/pdfs/{pdf_path}/chapters")
async def list_chapters(
    pdf_path: str,
):
    """List PDF chapters"""
    try:
        text = extract_pdf_text(pdf_path)
        text = preprocess_text(text)
        
        # Split into chunks
        chunks = split_into_chunks(text)
        chapters = []
        
        for i, chunk in enumerate(chunks):
            chapters.append({
                "num": i + 1,
                "title": f"Section {i + 1}",
                "start_page": i,
                "end_page": i,
                "word_count": len(chunk.split()),
                "estimated_duration": len(chunk) * 0.03  # Rough estimate
            })
        
        return {
            "pdf_path": pdf_path,
            "chapters": chapters
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# TTS Endpoints
@app.post("/api/v1/tts/generate")
async def generate_tts(request: TTSGenerateRequest):
    """Generate TTS audio"""
    try:
        samples, sr = generate_speech(request.text, request.voice, request.speed)
        samples = trim_silence(samples)
        samples = normalize_audio(samples)

        return {
            "audio_id": f"audio_{uuid4().hex[:12]}",
            "text": request.text,
            "voice": voice,
            "speed": speed,
            "duration_seconds": len(samples) / sr,
            "status": "completed",
            "audio_data": "BASE64_ENCODED AUDIO DATA"  # Placeholder
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/tts/split")
async def split_chunks(
    text: str,
    max_chars: int = 2000,
):
    """Split text into chunks"""
    try:
        chunks = split_into_chunks(text, max_chars)
        
        return {
            "chunks": [
                {"index": idx, "text": chunk, "length": len(chunk)}
                for idx, chunk in enumerate(chunks)
            ],
            "total_chunks": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Playback Endpoints
@app.post("/api/v1/playback/session")
async def create_playback_session(
    request: PlaybackSessionRequest,
    user_id: str = Header(...),
):
    """Create new playback session"""
    session_id = str(uuid4())
    state = PlaybackState()

    return {
        "session_id": session_id,
        "pdf_path": request.pdf_path,
        "chapter": request.chapter,
        "voice": request.voice,
        "speed": request.speed,
        "buffer_size": request.buffer_size,
        "status": "playing",
        "position": 0,
        "remaining": 0,
        "progress_percent": 0,
        "created_at": datetime.utcnow().isoformat()
    }

@app.patch("/api/v1/playback/{session_id}/pause")
async def toggle_pause(
    session_id: str,
    pause: bool = Query(...),
    user_id: str = Header(...),
):
    """Pause/resume playback"""
    # Placeholder for pause logic
    return {
        "session_id": session_id,
        "status": "paused" if pause else "playing"
    }

@app.patch("/api/v1/playback/{session_id}/seek")
async def seek_playback(
    session_id: str,
    offset: int = Query(...),
    user_id: str = Header(...),
    direction: str = "forward",
):
    """Seek playback"""
    return {
        "session_id": session_id,
        "new_position": offset,
        "formatted_position": fmt_time(offset)
    }

@app.delete("/api/v1/playback/{session_id}")
async def stop_playback(
    session_id: str,
    user_id: str = Header(...),
):
    """Stop playback session"""
    return {
        "session_id": session_id,
        "status": "stopped",
        "position_saved": True
    }

# Health Check
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "redis": "connected" if redis_client else "disconnected"
    }

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics"""
    return {
        "active_sessions": 0,
        "total_chunks_generated": 0,
        "total_playback_duration": 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("seferflow_api.main:app", host="0.0.0.0", port=8000)
