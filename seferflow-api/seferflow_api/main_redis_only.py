#!/usr/bin/env python3
"""
SeferFlow Web API - FastAPI Application (Redis-only storage)
Simplified version using only Redis for all data persistence.
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

# JWT is optional - we'll use dev tokens if not available
jwt = None

from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import redis

# Import seferflow engine
seferflow_dir = Path(__file__).parent.parent.parent
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
    description="PDF Audiobook Playback API - Redis-only storage",
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

# Redis Connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=5)
    redis_client.ping()
    print("✓ Redis connection established")
except Exception as e:
    print(f"✗ Redis connection failed: {e}")
    sys.exit(1)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "180"))

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

# Redis Storage Layer
class RedisStore:
    """Abstraction layer for Redis operations"""

    @staticmethod
    def user_key(email: str) -> str:
        return f"user:{email.lower()}"

    @staticmethod
    def user_id_key(user_id: str) -> str:
        return f"user_id:{user_id}"

    @staticmethod
    def session_key(session_id: str) -> str:
        return f"session:{session_id}"

    @staticmethod
    def progress_key(user_id: str, pdf_path: str) -> str:
        return f"progress:{user_id}:{pdf_path}"

    @staticmethod
    def create_user(email: str, username: str, hashed_password: str, role: str = "listener") -> Dict[str, Any]:
        """Create user in Redis"""
        user_id = f"user_{uuid4().hex[:12]}"
        user_data = {
            "user_id": user_id,
            "email": email,
            "username": username,
            "hashed_password": hashed_password,
            "role": role,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "tier": "free",
            "hours_used": "0",
        }
        redis_client.hset(RedisStore.user_key(email), mapping=user_data)
        redis_client.hset(RedisStore.user_id_key(user_id), mapping=user_data)
        return user_data

    @staticmethod
    def get_user(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        user = redis_client.hgetall(RedisStore.user_key(email))
        return user if user else None

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        user = redis_client.hgetall(RedisStore.user_id_key(user_id))
        return user if user else None

    @staticmethod
    def create_session(user_id: str, pdf_path: str, chapter: str, voice: str, speed: float, buffer_size: int = 6) -> Dict[str, Any]:
        """Create playback session"""
        session_id = str(uuid4())
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "pdf_path": pdf_path,
            "chapter": chapter,
            "voice": voice,
            "speed": str(speed),
            "buffer_size": str(buffer_size),
            "status": "ready",
            "position": "0",
            "created_at": datetime.utcnow().isoformat(),
        }
        # Expire after 24 hours
        redis_client.hset(RedisStore.session_key(session_id), mapping=session_data)
        redis_client.expire(RedisStore.session_key(session_id), 86400)
        return session_data

    @staticmethod
    def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Get playback session"""
        session = redis_client.hgetall(RedisStore.session_key(session_id))
        return session if session else None

    @staticmethod
    def update_session(session_id: str, **updates) -> bool:
        """Update session fields"""
        key = RedisStore.session_key(session_id)
        if not redis_client.exists(key):
            return False
        redis_client.hset(key, mapping=updates)
        return True

    @staticmethod
    def save_progress(user_id: str, pdf_path: str, chapter: str, last_chunk: int, total_chunks: int) -> bool:
        """Save progress"""
        key = RedisStore.progress_key(user_id, pdf_path)
        progress_data = {
            "pdf_path": pdf_path,
            "chapter": chapter,
            "last_chunk": str(last_chunk),
            "total_chunks": str(total_chunks),
            "progress_percent": str((last_chunk / total_chunks * 100) if total_chunks > 0 else 0),
            "updated_at": datetime.utcnow().isoformat(),
        }
        redis_client.hset(key, mapping=progress_data)
        return True

    @staticmethod
    def get_progress(user_id: str, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Get progress for a PDF"""
        key = RedisStore.progress_key(user_id, pdf_path)
        progress = redis_client.hgetall(key)
        return progress if progress else None


# Helper Functions
def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    if not jwt:
        return f"dev-token-{uuid4()}"
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    """Verify JWT and return user_id"""
    if not jwt:
        # For dev tokens, just return a dummy user_id
        if token.startswith("dev-token-"):
            return token.replace("dev-token-", "")
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None


# Auth Endpoints
@app.post("/api/v1/auth/register", status_code=201)
async def register_user(request: RegisterRequest):
    """Register new user"""
    # Check if user exists
    if RedisStore.get_user(request.email):
        raise HTTPException(status_code=400, detail="User already exists")

    # Validate password
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    # Hash password
    hashed_pw = hashlib.sha256(request.password.encode()).hexdigest()

    # Create user
    user_data = RedisStore.create_user(request.email, request.username, hashed_pw, request.role)
    token = create_access_token(user_data["user_id"])

    return {
        "user_id": user_data["user_id"],
        "email": request.email,
        "username": request.username,
        "role": request.role,
        "access_token": token,
        "created_at": user_data["created_at"],
        "message": "User registered successfully"
    }


@app.post("/api/v1/auth/login")
async def login(request: LoginRequest):
    """Login and get JWT token"""
    try:
        user = RedisStore.get_user(request.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Verify password
        hashed_pw = hashlib.sha256(request.password.encode()).hexdigest()
        if user.get("hashed_password") != hashed_pw:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token(user["user_id"])

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user["user_id"],
                "email": user["email"],
                "role": user.get("role", "listener"),
                "tier": user.get("tier", "free"),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/api/v1/auth/me")
async def get_current_user(authorization: str = Header(None)):
    """Get current user info"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")

    token = authorization.replace("Bearer ", "")
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = RedisStore.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user_id,
        "email": user["email"],
        "username": user["username"],
        "role": user["role"],
        "tier": user.get("tier", "free"),
        "hours_used": float(user.get("hours_used", 0)),
        "hours_remaining": 4.0 - float(user.get("hours_used", 0)),
    }


# PDF Endpoints
@app.get("/api/v1/pdfs/browse")
async def browse_pdfs(dir: str = "/home/mcstar/Nextcloud/Vault/books", authorization: str = Header(None)):
    """Browse PDF library"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization")

    books_dir = Path(dir)
    if not books_dir.exists():
        return {"contents": [], "path": str(books_dir)}

    contents = []
    for item in sorted(books_dir.iterdir()):
        if item.is_dir():
            contents.append({
                "name": item.name,
                "type": "directory",
                "path": str(item)
            })
        elif item.suffix.lower() == ".pdf":
            contents.append({
                "name": item.name,
                "type": "file",
                "path": str(item),
                "size": item.stat().st_size
            })

    return {"path": str(books_dir), "contents": contents}


@app.get("/api/v1/pdfs/{pdf_path:path}/chapters")
async def list_chapters(pdf_path: str, authorization: str = Header(None)):
    """List chapters in PDF"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization")

    try:
        chapters = get_chapters(pdf_path)
        return {"pdf_path": pdf_path, "chapters": chapters or []}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# TTS Endpoints
@app.post("/api/v1/tts/generate")
async def generate_tts(request: TTSGenerateRequest, authorization: str = Header(None)):
    """Generate TTS audio"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization")

    try:
        samples, sr = generate_speech(request.text, request.voice, request.speed)
        samples = trim_silence(samples)
        samples = normalize_audio(samples)

        return {
            "audio_id": f"audio_{uuid4().hex[:12]}",
            "text": request.text[:50] + "...",
            "voice": request.voice,
            "speed": request.speed,
            "sample_rate": sr,
            "duration": len(samples) / sr,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Playback Endpoints
@app.post("/api/v1/playback/session")
async def create_playback_session(request: PlaybackSessionRequest, authorization: str = Header(None)):
    """Create playback session"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization")

    token = authorization.replace("Bearer ", "")
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    session = RedisStore.create_session(user_id, request.pdf_path, request.chapter, request.voice, request.speed, request.buffer_size)
    return session


@app.get("/api/v1/playback/{session_id}")
async def get_playback_session(session_id: str, authorization: str = Header(None)):
    """Get playback session status"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization")

    session = RedisStore.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@app.patch("/api/v1/playback/{session_id}/pause")
async def toggle_pause(
    session_id: str,
    pause: bool = Query(...),
    authorization: str = Header(None),
):
    """Pause/resume playback"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization")

    session = RedisStore.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    new_status = "paused" if pause else "playing"
    RedisStore.update_session(session_id, status=new_status)

    return {"session_id": session_id, "status": new_status}


@app.patch("/api/v1/playback/{session_id}/seek")
async def seek_playback(
    session_id: str,
    offset: int = Query(...),
    authorization: str = Header(None),
    direction: str = "forward",
):
    """Seek playback position"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization")

    session = RedisStore.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    RedisStore.update_session(session_id, position=str(offset))

    return {
        "session_id": session_id,
        "position": offset,
        "formatted_position": fmt_time(offset)
    }


@app.delete("/api/v1/playback/{session_id}")
async def stop_playback(session_id: str, authorization: str = Header(None)):
    """Stop playback and cleanup"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization")

    session = RedisStore.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Expire session immediately
    redis_client.expire(RedisStore.session_key(session_id), 0)

    return {"session_id": session_id, "status": "stopped"}


# Progress Endpoints
@app.put("/api/v1/progress/{pdf_path:path}/{chapter}")
async def save_progress_endpoint(
    pdf_path: str,
    chapter: str,
    last_chunk: int = Query(...),
    total_chunks: int = Query(...),
    authorization: str = Header(None),
):
    """Save reading progress"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization")

    token = authorization.replace("Bearer ", "")
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    RedisStore.save_progress(user_id, pdf_path, chapter, last_chunk, total_chunks)

    return {
        "pdf_path": pdf_path,
        "chapter": chapter,
        "progress_percent": (last_chunk / total_chunks * 100) if total_chunks > 0 else 0,
    }


@app.get("/api/v1/progress")
async def get_all_progress(authorization: str = Header(None)):
    """Get all progress for user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization")

    token = authorization.replace("Bearer ", "")
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get all progress keys for this user
    pattern = f"progress:{user_id}:*"
    keys = redis_client.keys(pattern)
    progress_list = []

    for key in keys:
        progress = redis_client.hgetall(key)
        progress_list.append(progress)

    return {"progress": progress_list}


# Health Endpoints
@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "redis": "connected",
        "version": "1.0.0"
    }


@app.get("/api/v1/health")
async def api_health():
    """API health endpoint"""
    return {
        "status": "healthy",
        "storage": "redis",
        "version": "1.0.0"
    }


@app.get("/api/v1/metrics")
async def metrics():
    """Prometheus metrics placeholder"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
