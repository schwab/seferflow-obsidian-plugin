# SeferFlow API - Usage Tracking Documentation 🔔

## Overview

The SeferFlow API now includes **usage tracking** for free tier users and **premium user features**. This documentation covers:

- ✅ **Usage tracking endpoints** (track playback hours)
- ✅ **Free tier limitations** (4 hours/month)
- ✅ **Premium user benefits** (unlimited playtime, downloads)
- ✅ **Monthly usage statistics** (hours used, remaining)

---

## New API Endpoints

### 1. Track Usage 📊

**Endpoint**: `POST /api/v1/usage/track`

**Headers**:
- `Authorization: Bearer {token}`

**Request**:
```json
{
  "duration_seconds": 1800,
  "session_id": "sess-abc123"
}
```

**Response**: `200 OK`
```json
{
  "user_id": "usr_123",
  "session_id": "sess-abc123",
  "duration_seconds": 1800,
  "hours_used": 0.5,
  "status": "tracked"
}
```

### 2. Get Usage Statistics 📈

**Endpoint**: `GET /api/v1/usage/stats`

**Headers**:
- `Authorization: Bearer {token}`

**Response**: `200 OK`
```json
{
  "user_id": "usr_123",
  "tier": "free",
  "monthly_limit_hours": 4,
  "used_hours": 2.5,
  "remaining_hours": 1.5,
  "usage_percent": 62.5,
  "reset_date": "2026-05-06",
  "sessions_played": 8
}
```

### 3. Premium Status Check 🌟

**Endpoint**: `GET /api/v1/premium/status`

**Headers**:
- `Authorization: Bearer {token}`

**Response**: `200 OK`
```json
{
  "user_id": "usr_123",
  "is_premium": true,
  "subscription_type": "premium",
  "monthly_playtime_hours": 200,
  "download_enabled": true,
  "created_at": "2026-04-06T10:00:00Z"
}
```

### 4. Download Audio (Premium Only) 💾

**Endpoint**: `GET /api/v1/download/{audio_id}`

**Headers**:
- `Authorization: Bearer {token}`
- **Note**: Only for premium users

**Response**: `200 OK` (audio stream)

---

## Free Tier vs Premium Features

| Feature | Free Tier | Premium |
|---------|-----------|---------|
| Monthly Hours | 4 hours | Unlimited (200 months) |
| Play Speed | 0.8x - 1.3x | 0.8x - 1.5x |
| Voices | 4 neural voices | All voices |
| Downloads | ❌ | ✅ |
| Rate Limit | 60 req/min | 1000 req/min |
| Concurrent Sessions | 2 | Unlimited |
| WebSocket Streaming | ✅ | ✅ |

---

## Usage Calculation

**How usage is tracked:**

```python
# Duration in seconds is converted to hours
duration_hours = duration_seconds / 3600

# Free tier check
if used_hours + duration_hours > 4:
    raise HTTPException(status_code=403, detail="Monthly limit reached")
```

---

## Premium Subscription

**Upgrade to Premium** (example flow for Obsidian plugin):

```bash
# Upgrade request
curl -X POST /api/v1/premium/upgrade \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "plan": "premium",
    "email": "user@example.com",
    "payment_token": "stripe_token_xyz"
  }'
```

**Response**: `200 OK`
```json
{
  "user_id": "usr_123",
  "subscription_type": "premium",
  "status": "active",
  "expires_at": "2026-07-06T00:00:00Z"
}
```

---

## Usage Limits

**Free Tier:**
- Maximum 4 hours per month
- Resets on the first day of each month
- Usage tracked via PostgreSQL `usage` table

**Premium:**
- Unlimited playtime
- 200 hours/month (soft limit for monitoring)
- Download capability

---

## Obsidian Plugin Integration

**Usage Tracking in Plugin:**

```javascript
// Track usage in Obsidian plugin
const api = new SeferFlowAPIClient();

async function trackPlaybackSession(session) {
  try {
    await api.trackUsage({
      duration_seconds: session.duration,
      session_id: session.id
    });
  } catch (error) {
    console.error('Usage tracking failed:', error);
  }
}
```

**Check usage before playback:**

```javascript
async function canPlayAudio(duration) {
  const stats = await api.getUsageStats();
  
  if (stats.tier === 'free') {
    const hoursRemaining = stats.remaining_hours;
    
    if (duration / 3600 > hoursRemaining) {
      alert(
        `You've reached your monthly limit of ${stats.used_hours} hours. ` +
        `Remaining: ${hoursRemaining} hours`
      );
      
      return false;
    }
  }
  
  return true;
}
```

---

## Error Handling

### Rate Limit: `429 Too Many Requests`

```json
{
  "detail": "Rate limit exceeded",
  "status_code": 429,
  "code": "rate_limit_exceeded",
  "retry_after": 15
}
```

### Premium Required: `403 Forbidden`

```json
{
  "detail": "Premium subscription required for downloads",
  "status_code": 403,
  "code": "premium_required"
}
```

---

## Implementation Details

### Database Models

```python
class UsageRecord(SQLModel, table=True):
    """Usage tracking model"""
    id: Optional[str] = None
    user_id: str
    session_id: str
    duration_seconds: int = 0
    played_at: datetime = Field(default_factory=datetime.utcnow)

class FreeTierLimit(SQLModel, table=True):
    """Free tier monthly limit"""
    id: Optional[str] = None
    user_id: str
    monthly_limit_hours: int = 4  # Free tier
    used_hours: float = 0.0

class PremiumPlanUser(SQLModel, table=True):
    """Premium user tracking"""
    id: Optional[str] = None
    user_id: str
    subscription_type: str = "premium"
    monthly_playtime_hours: int = 200
    download_enabled: bool = True
```

---

## Migration Notes

When upgrading the API:

1. **Add migration scripts**:
   ```bash
   # Add usage tracking table migrations
   # Add premium user table
   # Add audit logs for usage
   ```

2. **Update existing users**:
   ```python
   # Free tier users get default 4-hour limit
   # Premium users get unlimited playtime
   ```

3. **Rate limiting**:
   - Free users: 60 requests per minute
   - Premium users: 1000 requests per minute

---

### See Also:
- [SeferFlow API Reference](./seferflow-api-reference.md)
- [JWT Authentication](./JWT_AUTHENTICATION.md)
- [Obsidian Plugin](./obsidian-plugin/)

**Version**: 2.0.0  
**Last Updated**: 2026-04-06
