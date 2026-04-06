# JWT-Based Authentication 🔐

**Last Updated**: 2026-04-06  
**Status**: ✅ Production-Ready for SeferFlow API v1.0

---

## What It Is

**JSON Web Token (JWT)** is an open standard (RFC 7519) that securely transmits information between parties as a **JSON object string**, digitally signed.

## 🆚 Traditional Sessions vs JWT

### 🛑 Traditional Session-Based Auth (Old Way)
```
Client → Server → Store Session in Database
Server → Query Database → Return Session Data
```
**Problems:**
- ❌ Requires database lookup per request
- ❌ Scalability limitation (one server = all sessions)
- ❌ Complex session management
- ❌ Memory-intensive

### ✅ JWT Authentication (Modern Way)
```
Client → Server → Generate JWT → Return to Client
Client → Send JWT in Request Header
Server → Verify Token Signature → Grant Access
```
**Benefits:**
- ✅ Stateless (no database lookup per request)
- ✅ Highly scalable (any server can handle any request)
- ✅ Easy to revoke (invalidate specific tokens in Redis)
- ✅ Works perfectly with REST APIs
- ✅ Perfect for microservices and distributed systems

## 🔐 How It Works

### 1️⃣ Login Request
```bash
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

### 2️⃣ Server Validates Credentials
- Checks password against database
- If valid → generates JWT token

### 3️⃣ JWT Structure
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "usr_123",
    "email": "user@example.com",
    "role": "listener",
    "exp": 1649347200,
    "iat": 1649336000
  },
  "signature": "base64Url(header.payload).sign(privateKey)"
}
```

### 4️⃣ Token Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 10800,
  "user": {
    "id": "usr_123",
    "email": "user@example.com",
    "role": "listener"
  }
}
```

## 📱 Using the JWT Token

### Subsequent Requests
```bash
# Include JWT in Authorization header
GET /api/v1/playback/session
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Types
- **Access Token**: Short-lived (3 hours) - for API calls
- **Refresh Token**: Long-lived (7 days) - to get new access token

## 🔧 For Your SeferFlow API

The API uses JWT authentication with:

```python
# Security Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ACCESS_TOKEN_EXPIRE_MINUTES = 180  # 3 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7
```

### 🔐 Password Security
```python
# Before issuing JWT, passwords are hashed
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"])

# Hash password
hashed_pw = pwd_context.hash(password)

# Verify password
pwd_context.verify(password, hashed_pw)
```

### 🆔 Token Content
```json
{
  "sub": "usr_123",         // User ID (claims)
  "email": "user@example.com",
  "role": "listener",
  "exp": 1649400600,        // Expiration time (unix timestamp)
  "iat": 1649336200,        // Issued at (unix timestamp)
  "jti": "token-uuid-123"   // Token ID (for revocation)
}
```

## 🔄 Refresh Token Flow

```
1. User accesses API → JWT expires (3 hours later)
2. Send refresh request with refresh token
3. Server issues new pair (access + refresh)
4. Never expire user sessions
```

## ⚠️ Security Best Practices

1. **HTTPS Only**: Never use JWT over HTTP
2. **Strong Keys**: Use at least 256-bit secrets
3. **Short Access Tokens**: 2-4 hours is perfect
4. **Refresh Tokens**: Rotate periodically
5. **HttpOnly Cookies**: Store tokens in cookies, not localStorage
6. **Token Revocation**: Blacklist tokens in Redis if needed

## 🎯 For SeferFlow API

```
┌─────────────┐
│   Client     │
│   Browser    │
└──────┬──────┘
       │ HTTP Request
       │ Authorization: Bearer {token}
       ▼
┌─────────────┐
│  API Server  │
│  (any worker │
│  in pool)    │
└──────┬──────┘
       │ Verify token
       │ with SECRET_KEY
       ▼
  Grant/Reject
```

**Benefits for audio streaming:**
- Multiple audio workers can serve playback requests
- No session synchronization needed
- Perfect for WebSocket streaming
- Easy to scale to handle many simultaneous users

## 🧩 API Implementation Example

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from datetime import datetime, timedelta
import secrets

# Configuration
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def verify_token(token: str):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@router.post("/api/v1/auth/login", response_model=Dict[str, Any])
async def login(username: str, password: str):
    """Login and get JWT token"""
    # Validate user...
    
    access_token = create_access_token(
        subject=username,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/api/v1/playback/session")
async def create_playback_session(user_id: str = Depends(get_current_user)):
    """Create new playback session"""
    # user_id comes from JWT token
    # No need to query user from database each request!
    pass

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token"""
    payload = await verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload
```

## 📚 References

- [JWT Specification (RFC 7519)](https://tools.ietf.org/html/rfc7519)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/first/)
- [JWT.io](https://jwt.io/) - Online JWT parser
- [Auth0 - JWT Guide](https://auth0.com/docs/identity-platform/guides/identity-and-access/jwts/whats-inside-a-jwt)

---

**Status**: ✅ Production-Ready  
**For Project**: SeferFlow Web API v1.0  
**Location**: `/home/mcstar/projects/seferflow/docs/`
