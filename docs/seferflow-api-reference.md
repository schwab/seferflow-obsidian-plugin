# SeferFlow Web API Reference 🚀📚🎤

## Overview

Production-ready REST API exposing every function from seferflow.py with:

- 🔐 **Authentication** - JWT-based with multi-user support
- 👥 **Multi-tenancy** - Isolated sessions per user
- ⚡ **Scalable Processing** - CPU/GPU workers for high throughput
- 📊 **WebSocket Support** - Real-time progress streaming
- 🎯 **Rate Limiting** - Per-user/request throttling
- 📈 **Metrics** - Prometheus metrics & health monitoring

---

## Quick Start

### Installation

```bash
cd /home/mcstar/projects/seferflow/seferflow-api
pip install -r requirements.txt
```

### Environment Variables

Create `.env` file:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
WORKERS=4

# Redis (Session Store)
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_DB=0

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=180
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate Limiting
RATE_LIMIT_MIN=60
RATE_LIMIT_HOUR=1000
RATE_LIMIT_BURST=10
RATE_LIMIT_LOGIN=5
RATE_LIMIT_REGISTER=3

# Worker Configuration
MAX_WORKERS=4
MAX_PROCESSES=8
ENABLE_CPU_WORKERS=true
ENABLE_GPU_WORKERS=false
GPU_DEVICE=0

# MCP Server
MCP_PORT=8765

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/seferflow/api.log
```

### Running the API

```bash
# Development
python -m uvicorn seferflow_api.main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  seferflow_api.main:app \
  -b 0.0.0.0:8000
```

---

## API Endpoints

### Base URL

```
http://localhost:8000/api/v1
```

---

## Authentication 🔐

### Register User

**Endpoint**: `POST /api/v1/auth/register`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "role": "listener"
}
```

**Response**: `201 Created`
```json
{
  "user_id": "usr_123",
  "email": "user@example.com",
  "username": "user",
  "role": "listener",
  "created_at": "2026-04-06T10:00:00Z",
  "message": "User registered successfully"
}
```

### Login

**Endpoint**: `POST /api/v1/auth/login`

**Headers**:
- `Content-Type: application/x-www-form-urlencoded`

**Request Body**:
```
username=user@example.com&password=SecurePass123!
```

**Response**: `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 10800,
  "user": {
    "id": "usr_123",
    "email": "user@example.com",
    "role": "listener",
    "status": "active"
  }
}
```

### Get Current User

**Endpoint**: `GET /api/v1/auth/me`

**Headers**:
- `Authorization: Bearer {access_token}`

**Response**: `200 OK`
```json
{
  "user": {
    "id": "usr_123",
    "email": "user@example.com",
    "username": "user",
    "role": "listener",
    "status": "active",
    "created_at": "2026-04-06T10:00:00Z",
    "last_login": "2026-04-06T10:53:00Z",
    "session_id": "abc-123-def-456"
  },
  "rate_limit_remaining": 59,
  "rate_limit_reset": "2026-04-06T11:00:00Z"
}
```

---

## PDF Operations 📚

### Browse PDF Library

**Endpoint**: `GET /api/v1/pdfs/browse`

**Query Parameters**:
- `dir` (required): Root directory path
- `page` (optional): Page number (0-based)
- `page_size` (optional): Items per page

**Headers**:
- `Authorization: Bearer {token}`

**Request**: `GET /api/v1/pdfs/browse?dir=/library`

**Response**: `200 OK`
```json
{
  "directory": "/library",
  "total_items": 150,
  "page": 0,
  "page_size": 10,
  "items": [
    {
      "id": "lib-abc",
      "type": "directory",
      "name": "Classics",
      "path": "/library/Classics",
      "status": "partial",
      "children_count": 25
    },
    {
      "id": "pdf-xyz",
      "type": "pdf",
      "name": "Harry_Potter.pdf",
      "path": "/library/Harry_Potter.pdf",
      "size_bytes": 15728640,
      "status": "partial",
      "chapters_count": 17
    }
  ]
}
```

### List PDF Chapters

**Endpoint**: `GET /api/v1/pdfs/{path}/chapters`

**Headers**:
- `Authorization: Bearer {token}`

**Request**: `GET /api/v1/pdfs/library/book.pdf/chapters`

**Response**: `200 OK`
```json
{
  "pdf_path": "library/book.pdf",
  "chapters": [
    {
      "num": 1,
      "title": "Chapter One",
      "start_page": 1,
      "end_page": 12,
      "word_count": 2500,
      "estimated_duration": 1800
    },
    {
      "num": 2,
      "title": "Chapter Two",
      "start_page": 14,
      "end_page": 28,
      "word_count": 2800,
      "estimated_duration": 2000
    }
  ]
}
```

### Get PDF Status

**Endpoint**: `GET /api/v1/pdfs/{path}/status`

**Request**: `GET /api/v1/pdfs/library/book.pdf/status`

**Response**: `200 OK`
```json
{
  "pdf_path": "library/book.pdf",
  "status": "partial",
  "chapters": {
    "Chapter One": {
      "last_chunk": 42,
      "total_chunks": 60,
      "listened_at": "2026-04-06T09:30:00Z"
    },
    "Chapter Two": {
      "last_chunk": 48,
      "total_chunks": 52,
      "listened_at": "2026-04-06T09:35:00Z"
    }
  }
}
```

### Get Chapter Progress

**Endpoint**: `GET /api/v1/pdfs/{path}/{chapter}/progress`

**Request**: `GET /api/v1/pdfs/library/book.pdf/Chapter%20One/progress`

**Response**: `200 OK`
```json
{
  "pdf_path": "library/book.pdf",
  "chapter": "Chapter One",
  "last_chunk": 42,
  "total_chunks": 60,
  "listened_at": "2026-04-06T09:30:00Z",
  "progress_percent": 70
}
```

---

## TTS Generation 🎤

### Generate TTS Audio

**Endpoint**: `POST /api/v1/tts/generate`

**Headers**:
- `Authorization: Bearer {token}`

**Request**:
```json
{
  "text": "Welcome to the audiobook! ☀️",
  "voice": "en-US-AriaNeural",
  "speed": 1.0,
  "sample_rate": 24000
}
```

**Response**: `200 OK`
```json
{
  "audio_id": "audio-abc123",
  "text": "Welcome to the audiobook! ☀️",
  "voice": "en-US-AriaNeural",
  "speed": 1.0,
  "sample_rate": 24000,
  "duration_seconds": 2.5,
  "status": "completed",
  "audio_url": "http://localhost:8000/api/v1/tts/audio/audio-abc123",
  "audio_data": "base64-encoded-wav-data"
}
```

### Split Text into Chunks

**Endpoint**: `POST /api/v1/tts/split`

**Headers**:
- `Authorization: Bearer {token}`

**Request**:
```json
{
  "text": "Welcome to the audiobook! ☀️ How are you today?",
  "max_chars": 2000
}
```

**Response**: `200 OK`
```json
{
  "chunks": [
    {
      "index": 0,
      "text": "Welcome to the audiobook! ☀️",
      "length": 35
    },
    {
      "index": 1,
      "text": "How are you today?",
      "length": 18
    }
  ],
  "total_chunks": 2
}
```

### List Cached Audio

**Endpoint**: `GET /api/v1/tts/cache`

**Headers**:
- `Authorization: Bearer {token}`

**Request**: `GET /api/v1/tts/cache?limit=10`

**Response**: `200 OK`
```json
{
  "cache": [
    {
      "id": "audio-abc123",
      "text": "Welcome to the audiobook!",
      "voice": "en-US-AriaNeural",
      "created_at": "2026-04-06T10:00:00Z",
      "expires_at": "2026-04-06T11:00:00Z"
    }
  ],
  "total": 15
}
```

### Download Cached Audio

**Endpoint**: `GET /api/v1/tts/audio/{id}`

**Headers**:
- `Authorization: Bearer {token}`

**Response**: `200 OK` (audio stream)

### Remove From Cache

**Endpoint**: `DELETE /api/v1/tts/cache/{id}`

**Headers**:
- `Authorization: Bearer {token}`

**Response**: `204 No Content`

---

## Playback Control 🎵

### Start Playback Session

**Endpoint**: `POST /api/v1/playback/session`

**Headers**:
- `Authorization: Bearer {token}`

**Request**:
```json
{
  "pdf_path": "library/book.pdf",
  "chapter": "Chapter One",
  "voice": "en-US-AriaNeural",
  "speed": 1.0,
  "buffer_size": 6,
  "websocket": true
}
```

**Response**: `201 Created`
```json
{
  "session_id": "sess-abc-123-def",
  "pdf_path": "library/book.pdf",
  "chapter": "Chapter One",
  "voice": "en-US-AriaNeural",
  "speed": 1.0,
  "buffer_size": 6,
  "status": "playing",
  "position": 0,
  "remaining": 1800,
  "progress_percent": 0,
  "created_at": "2026-04-06T10:53:00Z"
}
```

### Get Session Status

**Endpoint**: `GET /api/v1/playback/{session_id}`

**Headers**:
- `Authorization: Bearer {token}`

**Response**: `200 OK`
```json
{
  "session_id": "sess-abc-123-def",
  "pdf_path": "library/book.pdf",
  "chapter": "Chapter One",
  "voice": "en-US-AriaNeural",
  "speed": 1.0,
  "buffer_size": 6,
  "status": "playing",
  "position": 120,
  "formatted_position": "02:00",
  "remaining": 1680,
  "formatted_remaining": "28:00",
  "progress_percent": 6.67,
  "buffered": ● LIVE",
  "is_playing": true,
  "created_at": "2026-04-06T10:53:00Z",
  "paused_at": "2026-04-06T10:55:00Z"
}
```

### Pause/Resume

**Endpoint**: `PATCH /api/v1/playback/{session_id}/pause`

**Headers**:
- `Authorization: Bearer {token}`

**Request**:
```json
{
  "pause": true
}
```

**Response**: `200 OK`
```json
{
  "session_id": "sess-abc-123-def",
  "status": "paused",
  "position": 120,
  "paused_at": "2026-04-06T10:55:00Z"
}
```

### Seek Forward/Backward

**Endpoint**: `PATCH /api/v1/playback/{session_id}/seek`

**Headers**:
- `Authorization: Bearer {token}`

**Request**:
```json
{
  "offset": 5,
  "direction": "forward"
}
```

**Response**: `200 OK`
```json
{
  "session_id": "sess-abc-123-def",
  "new_position": 125,
  "formatted_position": "02:05"
}
```

### Stop Session

**Endpoint**: `DELETE /api/v1/playback/{session_id}`

**Headers**:
- `Authorization: Bearer {token}`

**Response**: `200 OK`
```json
{
  "session_id": "sess-abc-123-def",
  "status": "stopped",
  "position_saved": true
}
```

---

## MCP Interruption ⚡

### Inject Message

**Endpoint**: `POST /api/v1/mcp/say`

**Headers**:
- `Authorization: Bearer {token}`

**Request**:
```json
{
  "text": "Good morning everyone! ☀️ ☕",
  "voice": "en-US-AriaNeural",
  "priority": "high"
}
```

**Response**: `200 OK`
```json
{
  "message_id": "msg-abc123",
  "text": "Good morning everyone! ☀️ ☕",
  "voice": "en-US-AriaNeural",
  "priority": "high",
  "status": "playing",
  "duration_seconds": 3.0,
  "note": "Injected message will interrupt current playback"
}
```

### List MCP Tools

**Endpoint**: `POST /api/v1/mcp/list`

**Headers**:
- `Authorization: Bearer {token}`

**Request**: `{"jsonrpc": "2.0", "method": "tools/list"}`

**Response**: `200 OK`
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "say_text",
        "description": "Interrupt current audiobook and speak given text aloud, then resume.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "text": {
              "type": "string",
              "description": "Text to speak"
            },
            "voice": {
              "type": "string",
              "description": "edge-tts voice name (optional)"
            }
          },
          "required": ["text"]
        }
      }
    ]
  }
}
```

### Call MCP Tool

**Endpoint**: `POST /api/v1/mcp/call`

**Headers**:
- `Authorization: Bearer {token}`

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "arguments": {
      "text": "Please pause for a moment!",
      "voice": "en-US-AriaNeural"
    }
  }
}
```

**Response**: `200 OK`
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Message injected successfully"
      }
    ]
  }
}
```

---

## Progress Tracking 📊

### Save Progress

**Endpoint**: `PUT /api/v1/progress/{pdf_path}/{chapter}`

**Headers**:
- `Authorization: Bearer {token}`

**Request**:
```json
{
  "last_chunk": 45,
  "total_chunks": 60
}
```

**Response**: `200 OK`
```json
{
  "pdf_path": "library/book.pdf",
  "chapter": "Chapter One",
  "last_chunk": 45,
  "total_chunks": 60,
  "update_time": "2026-04-06T10:55:00Z"
}
```

### Get All Progress

**Endpoint**: `GET /api/v1/progress`

**Headers**:
- `Authorization: Bearer {token}`

**Response**: `200 OK`
```json
{
  "pdfs": [
    {
      "pdf_path": "library/book.pdf",
      "chapters": {
        "Chapter One": {
          "last_chunk": 45,
          "total_chunks": 60,
          "progress_percent": 75,
          "listened_at": "2026-04-06T10:55:00Z"
        }
      },
      "file_status": "partial"
    }
  ]
}
```

### Playback History

**Endpoint**: `GET /api/v1/progress/history`

**Headers**:
- `Authorization: Bearer {token}`

**Request**: `GET /api/v1/progress/history?limit=10`

**Response**: `200 OK`
```json
{
  "history": [
    {
      "session_id": "sess-abc123",
      "pdf_path": "library/book.pdf",
      "chapter": "Chapter One",
      "started_at": "2026-04-06T10:00:00Z",
      "stopped_at": "2026-04-06T12:00:00Z",
      "duration_seconds": 7200
    }
  ],
  "total": 15
}
```

---

## WebSocket Streaming 📡

### Connect to Playback Room

**Endpoint**: `wss://api.seferflow.local/ws/progress/{session_id}`

**Protocol**: WebSocket

**Message Format**:

```json
{
  "type": "progress_update",
  "data": {
    "session_id": "sess-abc-123-def",
    "position": 125,
    "formatted_position": "02:05",
    "remaining": 1675,
    "formatted_remaining": "27:55",
    "progress_percent": 6.79,
    "buffered": "● LIVE",
    "is_playing": true,
    "timestamp": "2026-04-06T10:55:00Z"
  }
}
```

### WebSocket Rooms

| Room | Description |
|------|-------------|
| `/ws/progress/{session_id}` | Real-time progress updates |
| `/ws/player/{session_id}` | Stream audio chunks |
| `/ws/mcp` | MCP interruption events |

---

## System Health & Metrics 🏥

### Health Check

**Endpoint**: `GET /api/v1/health`

**Headers**: None (public endpoint)

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-04-06T10:53:00Z",
  "services": {
    "redis": "connected",
    "database": "connected",
    "mcp": "running"
  },
  "uptime_seconds": 3600
}
```

### Metrics

**Endpoint**: `/metrics`

**Headers**: None (Prometheus scraping)

**Response**: Prometheus HTTP text exposition format

```
# HELP seferflow_active_sessions Active playback sessions
# TYPE seferflow_active_sessions gauge
seferflow_active_sessions 3

# HELP seferflow_tts_chunks_generated Total TTS chunks generated
# TYPE seferflow_tts_chunks_generated counter
seferflow_tts_chunks_generated 15842

# HELP seferflow_playback_duration_total Total playback duration in seconds
# TYPE seferflow_playback_duration_total counter
seferflow_playback_duration_total 125000

# HELP seferflow_cpu_usage_seconds_total CPU usage over time
# TYPE seferflow_cpu_usage_seconds_total counter
seferflow_cpu_usage_seconds_total 25400

# HELP seferflow_memory_bytes_used Memory usage in bytes
# TYPE seferflow_memory_bytes_bytes gauge
seferflow_memory_bytes_used 536870912
```

---

## Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Successful request |
| 201 | Created | Resource created |
| 204 | No Content | Success with no response |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Session already exists |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

---

## Error Handling

All errors return JSON format:

```json
{
  "detail": "Error message",
  "status_code": 401,
  "code": "invalid_token",
  "timestamp": "2026-04-06T10:55:00Z"
}
```

**Common Error Codes**:

- `invalid_token` - JWT invalid or expired
- `session_not_found` - Session does not exist
- `user_banned` - User account banned
- `rate_limit_exceeded` - Too many requests
- `invalid_request` - Invalid request parameters

---

## Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| Login/Register | 5 | 1 minute |
| Audio Generation | 30 | 1 minute |
| Playback Control | 60 | 1 minute |
| General API | 60 | 1 minute |
| WebSocket | Unlimited | - |

Rate limit headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1649347200
```

---

## File Upload

### Upload Custom Audio

**Endpoint**: `POST /api/v1/upload/audio`

**Headers**:
- `Authorization: Bearer {token}`
- `Content-Type: multipart/form-data`

**Request**: Upload WAV file

**Response**: `200 OK`
```json
{
  "upload_id": "upload-abc123",
  "filename": "custom_audio.wav",
  "size_bytes": 5242880,
  "upload_time": "2026-04-06T10:55:00Z"
}
```

---

## Voice Options

Supported edge-tts voices:

| Code | Voice | Description |
|------|-------|-------------|
| aria | en-US-AriaNeural | Female US |
| guy | en-US-GuyNeural | Male US |
| libby | en-GB-LibbyNeural | Female British |
| ryan | en-GB-RyanNeural | Male British |

---

## Examples

### Create Playback Session

```bash
curl -X POST http://localhost:8000/api/v1/playback/session \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_path": "library/book.pdf",
    "chapter": "Chapter One",
    "voice": "en-US-AriaNeural",
    "speed": 1.0,
    "buffer_size": 6
  }'
```

### Inject Message via MCP

```bash
curl -X POST "http://localhost:8000/api/v1/mcp/say" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Remember to drink water! 💧",
    "voice": "en-US-AriaNeural",
    "priority": "high"
  }'
```

### Pause Playback

```bash
curl -X PATCH "http://localhost:8000/api/v1/playback/sess-abc/pause" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pause": true}'
```

---

## API Version

**Version**: 1.0.0  
**Last Updated**: 2026-04-06  
**Documentation**: https://docs.seferflow.local

---

## Support

For issues or questions:

- 📚 **GitHub Issues**: https://github.com/seferflow/seferflow-api/issues
- 📚 **Documentation**: https://docs.seferflow.local
