#!/usr/bin/env python3
"""Minimal SeferFlow API for plugin testing"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import uuid
from pathlib import Path

app = FastAPI(
    title="SeferFlow API (Dev)",
    description="Minimal API for plugin testing",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class User(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str

# In-memory storage (for testing)
users_db = {}
sessions_db = {}

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "version": "0.1.0"}

@app.post("/api/v1/auth/register")
async def register(user: User):
    """Register new user"""
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="User already exists")

    user_id = str(uuid.uuid4())
    users_db[user.email] = {
        "id": user_id,
        "email": user.email,
        "password": user.password,  # In production: hash this!
    }

    return {
        "user_id": user_id,
        "email": user.email,
        "message": "User registered successfully"
    }

@app.post("/api/v1/auth/login")
async def login(credentials: LoginRequest):
    """Login and get JWT token"""
    user = users_db.get(credentials.email)
    if not user or user["password"] != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = f"dev-token-{uuid.uuid4()}"
    sessions_db[token] = {
        "user_id": user["id"],
        "email": user["email"]
    }

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user["id"]
    )

@app.get("/api/v1/auth/me")
async def get_me(authorization: str = None):
    """Get current user info"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")

    token = authorization.replace("Bearer ", "")
    session = sessions_db.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "user_id": session["user_id"],
        "email": session["email"],
        "tier": "free",
        "hours_remaining": 4.0
    }

@app.get("/api/v1/pdfs/browse")
async def browse_pdfs(dir: str = "/home/mcstar/Nextcloud/Vault/books", authorization: str = None):
    """Browse PDF library"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")

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

    return {
        "path": str(books_dir),
        "contents": contents
    }

@app.get("/api/v1/pdfs/{pdf_path}/chapters")
async def list_chapters(pdf_path: str, authorization: str = None):
    """List chapters in PDF"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")

    # Placeholder - real implementation would extract PDF chapters
    return {
        "pdf_path": pdf_path,
        "chapters": [
            {"title": "Chapter 1", "index": 0, "pages": "1-20"},
            {"title": "Chapter 2", "index": 1, "pages": "21-45"},
            {"title": "Chapter 3", "index": 2, "pages": "46-70"},
        ]
    }

@app.post("/api/v1/tts/generate")
async def generate_tts(text: str, voice: str = "en-US-AriaNeural", speed: float = 1.0, authorization: str = None):
    """Generate TTS audio"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")

    return {
        "status": "generating",
        "text": text[:50] + "...",
        "voice": voice,
        "speed": speed,
        "duration_seconds": len(text) / 100 * (1 / speed)  # Estimate
    }

@app.post("/api/v1/playback/session")
async def create_playback_session(pdf_path: str, chapter: str, voice: str, speed: float, authorization: str = None):
    """Create playback session"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")

    session_id = str(uuid.uuid4())
    return {
        "session_id": session_id,
        "pdf_path": pdf_path,
        "chapter": chapter,
        "voice": voice,
        "speed": speed,
        "status": "ready"
    }

@app.get("/api/v1/metrics")
async def metrics():
    """Prometheus metrics"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
