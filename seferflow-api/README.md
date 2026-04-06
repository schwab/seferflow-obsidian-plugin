SeferFlow Web API ⚡📚🎤

🎯 **Mission**: Expose every function from seferflow.py as REST API endpoints with authentication, multi-user support, and scalable CPU/GPU processing.

---

## 🚀 Quick Start

### 1. Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and edit config
cp .env.example .env
nano .env        # Set secrets, Redis, GPU settings
```

### 2. Run API Server

```bash
# Development (threaded)
python -m uvicorn seferflow_api.main:app --reload --host 0.0.0.0 --port 8000

# Production (Gunicorn + multiple workers)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  seferflow_api.main:app \
  -b 0.0.0.0:8000 \
  --timeout 300 \
  --graceful-timeout 60
```

### 3. API Documentation

```bash
# Open Swagger UI
curl http://localhost:8000/docs

# Open ReDoc
curl http://localhost:8000/redoc
```

### 4. Docker Compose

```bash
docker-compose up -d
```

---

## 🔑 API Endpoints

### **Authentication** 🔐

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/auth/register` | ✗ | Register new user |
| `POST` | `/api/v1/auth/login` | ✗ | Login + JWT token |
| `POST` | `/api/v1/auth/logout` | ✓ | Invalidate token |
| `GET` | `/api/v1/auth/me` | ✓ | Current user info |
| `GET` | `/api/v1/auth/whoami` | ✓ | User session info |

### **PDF Operations** 📚

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/pdfs/browse?dir={path}` | ✓ | Browse PDF library |
| `GET` | `/api/v1/pdfs/{path}/chapters` | ✓ | List PDF chapters |
| `GET` | `/api/v1/pdfs/{path}/status` | ✓ | File/Directory progress |
| `GET` | `/api/v1/pdfs/{path}/{ch}/progress` | ✓ | Chapter progress details |

### **TTS Generation** 🎤

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/tts/generate` | ✓ | Generate TTS audio |
| `GET` | `/api/v1/tts/chunks` | ✓ | List text chunks |
| `POST` | `/api/v1/tts/split` | ✓ | Split text by sentences |
| `GET` | `/api/v1/tts/cache` | ✓ | Cached audio chunks |
| `DELETE` | `/api/v1/tts/cache/{key}` | ✓ | Remove cache |

### **Playback** 🎵

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/playback/session` | ✓ | Start playback session |
| `GET` | `/api/v1/playback/{session_id}` | ✓ | Session status |
| `PATCH` | `/api/v1/playback/{session_id}/pause` | ✓ | Pause/resume |
| `PATCH` | `/api/v1/playback/{session_id}/seek` | ✓ | Seek to position |
| `DELETE` | `/api/v1/playback/{session_id}` | ✓ | Stop & cleanup |

### **MCP Interruption** ⚡

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/mcp/say` | ✓ | Inject message |
| `POST` | `/api/v1/mcp/list` | ✓ | List MCP tools |
| `POST` | `/api/v1/mcp/call` | ✓ | Call MCP tool |

### **Progress Tracking** 📊

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `PUT` | `/api/v1/progress/{path}/{ch}` | ✓ | Save progress |
| `GET` | `/api/v1/progress` | ✓ | All progress |
| `GET` | `/api/v1/progress/history` | ✓ | Playback history |

### **System Health** 🏥

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/health` | ✗ | API health check |
| `GET` | `/api/v1/metrics` | ✗ | Prometheus metrics |

---

## 🎯 Examples

### **Browse PDF Library**
```bash
curl -X GET "http://localhost:8000/api/v1/pdfs/browse?dir=/home/mcstar/projects/seferflow/library" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **List Chapters**
```bash
curl -X GET "http://localhost:8000/api/v1/pdfs/library/book.pdf/chapters" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **Generate TTS Chunk**
```bash
curl -X POST "http://localhost:8000/api/v1/tts/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Welcome to the audiobook!",
    "voice": "en-US-AriaNeural",
    "speed": 1.0
  }'
```

### **Start Playback Session**
```bash
curl -X POST "http://localhost:8000/api/v1/playback/session" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_path": "/home/mcstar/projects/seferflow/library/book.pdf",
    "chapter": "Chapter 1",
    "voice": "en-US-AriaNeural",
    "speed": 1.0,
    "buffer_size": 6
  }'
```

### **Interruption (MCP Message)**
```bash
# Inject a message during playback
curl -X POST "http://localhost:8000/api/v1/mcp/say" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Good afternoon everyone! ☀️",
    "voice": "en-US-AriaNeural",
    "priority": "high"
  }'
```

### **Save Progress**
```bash
curl -X PUT "http://localhost:8000/api/v1/progress/library/book.pdf/Chapter%201" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "last_chunk": 42,
    "total_chunks": 120
  }'
```

---

## 🔒 Security

### **Authentication**
- **JWT Tokens**: Access tokens (3h), Refresh tokens (7d)
- **Password Policy**: Min 8 chars, 1 upper, 1 lower, 1 digit, 1 vowel, 1 consonant
- **Rate Limiting**: 60 req/min per user
- **Session Management**: Redis-backed session store

### **Encryption**
- TLS/HTTPS in production
- Passwords hashed with bcrypt
- JWT signed with RS256/HS256

---

## 🧠 Scalability

### **Worker Architecture**

```
┌─────────────────────────────────────┐
│       API Gateway (FastAPI)         │
│  Auth | PDF | TTS | Playback | MCP  │
└─────────────────────────────────────┘
              │
              ▼
    ┌───────────────────────────────┐
    │   Redis (Session Store)       │
    │   Queue (Celery/RQ)           │
    └───────────────────────────────┘
              │
    ┌─────────┴─────────┐
    ▼                   ▼
TTS Workers    Audio Players
(Generate)     (Playback)
    │                   │
    └─────────┬─────────┘
              ▼
        Redis Queue
              │
    ┌─────────┴─────────┐
    ▼                   ▼
  GPU Workers    Cleanup Workers
(Heavy)         (Session End)
```

### **Auto-Scaling**
- CPU: Based on queue depth (>80% load → scale up)
- GPU: Dedicated CUDA streams per session
- Cleanup: Sessions cleaned after user logout

---

## 📊 Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created (session) |
| `204` | No Content (delete) |
| `400` | Bad Request |
| `401` | Unauthorized |
| `403` | Forbidden |
| `404` | Not Found |
| `429` | Too Many Requests |
| `500` | Internal Server Error |
| `503` | Service Unavailable |

---

## 📦 Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
      - "9000:9000"  # Metrics
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://...
      - MAX_WORKERS=4
      - ENABLE_GPU=true
    depends_on:
      - redis
      - db

  redis:
    image: redis:7-alpine

  db:
    image: postgres:15
```

---

**Version**: 1.0.0  
**Last Updated**: 2026-04-06