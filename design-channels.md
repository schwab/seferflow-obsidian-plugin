# SeferFlow Multi-Channel System Design 📑🎵📺

## Overview

A multi-channel audio routing system where users can have **n concurrent text-audio channels** connected to their account. Each channel is mapped to a specific UI instance and identified by a persistent ID.

---

## 🎯 Channel Architecture

### What is a "Channel"?

A channel represents **one playback session client** for a user:
- Obsidian vault plugin instance
- Terminal-based UI (TUI) instance
- Web browser UI instance
- Mobile app instance (future)

Each channel:
- Is associated with a specific user
- Has a persistent ID (stored in database)
- Can receive targeted or broadcast messages
- Tracks active/inactive status

---

## 🗄️ Database Models

### Channel Model

```python
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime, Enum

class Channel(SQLModel, table=True):
    __tablename__ = "channels"
    
    # Primary key
    id: str = Field(primary_key=True)  # Persistent channel ID
    
    # User association
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Channel metadata
    name: str = Field(index=True)  # Display name
    type: str = Field(index=True)  # "obsidian", "tui", "web", "mobile"
    description: str = Field(sa_column_kwargs={"default": ""})
    
    # Technical details
    host_id: str | None = Field(sa_column_kwargs={"default": None})
    device_id: str | None = Field(sa_column_kwargs={"default": None})
    version: str = Field(default="unknown")
    
    # Status tracking
    is_active: bool = Field(default=True)
    last_seen: datetime = Field(default_factory=lambda: datetime.utcnow())
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    
    # Usage tracking
    playback_hours_total: float = Field(default=0.0)
    interruptions_received: int = Field(default=0)
    
    @property
    def is_online(self) -> bool:
        """Check if channel has been seen recently"""
        # Mark inactive if last seen > 5 minutes ago
        return (datetime.utcnow() - self.last_seen).seconds < 300
```

### Channel Status Model

```python
class ChannelStatus(SQLModel, table=True):
    __tablename__ = "channel_status"
    
    id: str = Field(primary_key=True)
    channel_id: str = Field(foreign_key="channels.id", index=True)
    
    # Status metadata
    status: str = Field(default="active")  # active, inactive, paused, error
    message: str = Field(sa_column_kwargs={"default": ""})
    
    # Timestamps
    recorded_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    
    class Config:
        table: str = "channel_status"
```

### Message Log Model

```python
class MessageLogEntry(SQLModel, table=True):
    __tablename__ = "message_logs"
    
    id: str = Field(primary_key=True)
    channel_id: str = Field(foreign_key="channels.id")
    user_id: str = Field(foreign_key="users.id")
    text: str
    sender: str | None = None
    message_type: str = Field(default="interruption")  # interruption, notification
    
    # Metadata
    duration_seconds: int = 0
    is_delivered: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
```

---

## 🔌 API Endpoints for Channels

### 1. Register Channel

```python
@app.post("/api/v1/channels/register")
async def register_channel(
    channel_request: ChannelRegisterRequest,
    user_id: str = Depends(get_current_user),
):
    """Register a new playback channel"""
    
    # Check user limit
    user_channels = select(Channel).where(
        Channel.user_id == user_id,
        Channel.is_active == True
    ).count()
    
    if user_channels >= MAX_CHANNELS_PER_USER:
        raise HTTPException(status_code=429, detail="Channel limit reached")
    
    # Create channel ID (persistent)
    channel_id = generate_persistent_channel_id(
        user_id=user_id,
        channel_type=channel_request.type,
        device_host=channel_request.host_id,
    )
    
    # Create channel record
    new_channel = Channel(
        id=channel_id,
        user_id=user_id,
        name=channel_request.name,
        type=channel_request.type,
        host_id=channel_request.host_id,
        device_id=channel_request.device_id,
        description=channel_request.description,
    )
    
    db.add(new_channel)
    db.commit()
    
    return new_channel


class ChannelRegisterRequest(BaseModel):
    name: str
    type: ChannelType
    description: Optional[str] = ""
    host_id: Optional[str] = None
    device_id: Optional[str] = None
```

### 2. List Channels

```python
@app.get("/api/v1/channels", response_model=List[Channel])
async def list_channels(
    user_id: str = Depends(get_current_user),
):
    """List all channels for current user"""
    
    channels = select(Channel).where(
        Channel.user_id == user_id
    ).order_by(Channel.updated_at.desc()).all()
    
    return channels
```

### 3. Broadcast Message

```python
@app.post("/api/v1/channels/broadcast")
async def broadcast_message(
    message: MessageBroadcastRequest,
    channel_ids: Optional[List[str]] = None,
    message: dict = None,
):
    """Broadcast to specified channels or all active channels"""
    
    if not message:
        raise HTTPException(status_code=400, detail="Message content required")
    
    # Get target channels
    target_channels = []
    
    if channel_ids:
        # Specific channels
        target_channels = select(Channel).where(
            Channel.is_active == True,
            Channel.id.in_(channel_ids),
            Channel.user_id == message.user_id  # Verify ownership
        ).all()
    else:
        # All active for user
        if message.user_id is None:
            # Broadcast to all users (admin mode only)
            target_channels = select(Channel).where(
                Channel.is_active == True
            )
        else:
            # All active for specific user
            target_channels = select(Channel).where(
                Channel.is_active == True,
                Channel.user_id == message.user_id
            ).all()
    
    # Log and notify each channel
    results = []
    for channel in target_channels:
        # Send notification
        if send_notification(channel.host_id, channel.device_id, message):
            results.append({
                "channel_id": channel.id,
                "success": True,
                "message_type": message.type,
            })
            # Track usage
            channel.playback_hours_total += message.duration_seconds
            channel.interruptions_received += 1
            channel.last_seen = datetime.utcnow()
        else:
            # Channel unreachable
            pass
    
    return results
```

### 4. Heartbeat/Keep Alive

```python
@app.post("/api/v1/channels/{channel_id}/heartbeat")
async def channel_heartbeat(
    channel_id: str,
    host_id: str = Header(...),
):
    """Mark channel as active to keep it alive in system"""
    
    channel = select(Channel).where(
        Channel.id == channel_id,
        Channel.user_id == get_current_user(...).id,
    ).first()
    
    if not channel or not channel.is_active:
        raise HTTPException(status_code=404, detail="Channel not found or inactive")
    
    # Update channel status
    channel.last_seen = datetime.utcnow()
    channel.updated_at = datetime.utcnow()
    
    return {"channel_id": channel_id, "status": "active"}
```

### 5. Update Channel Status

```python
@app.post("/api/v1/channels/{channel_id}/status")
async def update_channel_status(
    channel_id: str,
    status_update: StatusUpdateRequest,
):
    """Update channel status (active/inactive/error)"""
    
    channel = db.get(Channel, channel_id)
    
    if not channel:
        raise HTTPException(status_code=404)
    
    # Update status
    channel.is_active = status_update.is_active
    channel.status = status_update.status
    
    return channel
```

---

## 🔄 Heartbeat System

### Implementation

```python
class ChannelHeartbeatManager:
    """Manage channel heartbeats and activity tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def heartbeat(self, channel_id: str) -> bool:
        """Mark channel as active"""
        try:
            channel = self.db.get(Channel, channel_id)
            if channel and channel.is_active:
                channel.last_seen = datetime.utcnow()
                channel.updated_at = datetime.utcnow()
                self.db.commit()
                return True
        except Exception as e:
            # Log heartbeat failure
            pass
        return False
    
    def cleanup_inactive_channels(self, threshold_seconds: int = 300):
        """Remove or deactivate channels that haven't responded"""
        cutoff = datetime.utcnow() - timedelta(seconds=threshold_seconds)
        
        inactive_count = 0
        for channel in self.db.query(Channel).filter(
            Channel.last_seen < cutoff
        ).all():
            channel.is_active = False
            channel.last_seen = cutoff
            inactive_count += 1
        
        self.db.commit()
        return inactive_count
```

### Scheduled Cleanup

```python
@celery.task
def cleanup_inactive_channels():
    """Background task to clean up inactive channels"""
    return ChannelHeartbeatManager(db).cleanup_inactive_channels()
```

---

## 📊 Message Delivery Logic

### Broadcast vs Targeted

```python
def deliver_message(
    message: Message,
    channel_ids: Optional[List[str]] = None,
):
    """
    Deliver message to channels.
    
    If no channel IDs: deliver to all active channels for user
    If channel IDs: deliver only to specified channels
    
    Returns list of delivery results
    """
    user = get_current_user_from_message(message)
    messages = message.message
    target_ids = channel_ids or []
    
    if not target_ids:
        # Get all active channels for user
        target_ids = [channel.id for channel in 
                      select(Channel).where(
                          Channel.user_id == user.id,
                          Channel.is_active == True
                      ).all()]
    
    results = []
    for channel_id in target_ids:
        # Get channel
        channel = select(Channel).where(Channel.id == channel_id).first()
        
        # Send to channel
        if send_to_channel(channel, message):
            results.append({
                "channel_id": channel_id,
                "delivered": True,
                "timestamp": datetime.utcnow()
            })
        else:
            results.append({
                "channel_id": channel_id,
                "delivered": False,
                "error": "Channel unavailable",
                "timestamp": datetime.utcnow()
            })
    
    return results
```

---

## 🔄 MCP Integration

### MCP Tool for Message Delivery

```python
from pydantic import BaseModel, Field

class SayTextParams(BaseModel):
    """MCP tool parameters for interrupting playback"""
    text: str = Field(description="Text to speak")
    voice: Optional[str] = "en-US-AriaNeural"
    channel_id: str = Field(
        default="",
        description="Channel ID to interrupt, or empty for broadcast"
    )
    priority: str = Field(default="normal", description="high|normal|low")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Please take a break! ⛔",
                "voice": "en-US-AriaNeural",
                "channel_id": "channel_123456",  # or empty for all channels
                "priority": "high"
            }
        }
    
    text: str
    voice: str = "en-US-AriaNeural"
    channel_id: str = ""
    priority: str = "normal"

class SayTextResult(BaseModel):
    success: bool = Field(description="Was message delivered?")
    channels_interrupted: List[int] = Field(description="Number of channels interrupted")
    duration_seconds: int
    timestamp: str
```

```python
@app.post("/api/v1/mcp/say")
async def mcp_interrupt_message(
    tool_call: ToolCallRequest,
    params: SayTextParams,
):
    """MCP tool for interrupting playback in channels"""
    
    # Create message
    message = Message(
        text=params.text,
        voice=params.voice,
        channel_id=params.channel_id or None,  # None = broadcast
        priority=params.priority,
    )
    
    # Deliver to channels
    results = await broadcast_message(message)
    
    return SayTextResult(
        success=True,
        channels_interrupted=len(results),
        duration_seconds=len(params.text),
        timestamp=datetime.utcnow().isoformat(),
    )
```

---

## 📖 Status Tracking System

### Active Channels View

```python
@app.get("/api/v1/channels/status")
async def get_channel_status(
    user_id: str = Depends(get_current_user),
):
    """Get all channels status"""
    
    channels = select(Channel).where(
        Channel.user_id == user_id,
        Channel.is_active == True
    ).all()
    
    return {
        "active_channels": len(channels),
        "channels": [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "status": "active" if c.last_seen > threshold else "inactive",
                "last_seen": c.last_seen.isoformat(),
            } for c in channels
        ]
    }
```

---

## 🔐 Security Considerations

### Channel Ownership Verification

All channel operations must verify:
```python
def verify_channel_ownership(channel_id: str, user_id: str):
    """Verify channel belongs to user"""
    channel = db.get(Channel, channel_id)
    if channel and channel.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return True
```

### Rate Limiting

```python
# Prevent abuse
@app.post("/api/v1/channels/register")
async def register_channel(
    request: RegisterChannel,
    headers: dict = Header(...),
):
    # Rate limit check
    client_ip = headers.get("x-forwarded-for", "")
    rate_limiter.check_rate_limit(client_ip)
    # ...
```

---

## 📊 Monitoring & Analytics

```python
class ChannelAnalytics:
    """Track channel usage and health"""
    
    def get_daily_stats(self) -> dict:
        """Daily analytics"""
        stats = {
            "total_channels": select(func.count(Channel.id)).scalar(),
            "active_channels": select(func.count(Channel)).where(Channel.is_active == True).scalar(),
            "messages_sent": select(func.sum(Message.interruptions_received)).scalar(),
            "avg_duration": select(func.avg(Message.duration_seconds)).scalar(),
        }
        return stats
```

---

## 🔄 Migration Considerations

### Existing Channels

When migration happens:
```python
def migrate_existing_users(db: Session):
    """Migrate existing users to channel system"""
    for user in select(User).all():
        channels = Channel.select().where(Channel.user_id == user.id)
        for channel in channels:
            # Assign persistent ID based on user + device
            channel.id = generate_channel_id(channel.id)
            channel.type = detect_channel_type(channel)
```

---

## 📖 Summary

This channel system allows:

1. **Multiple simultaneous playback** for single user
2. **Persistent channel IDs** across restarts
3. **Targeted messages** to specific channels
4. **Broadcast to all active** user channels
5. **Heartbeat tracking** for active/inactive status
6. **MCP interruption routing** with channel awareness

**Key design principles:**

- **Channel persistence**: IDs never change
- **Heartbeat system**: Channels must prove they're active
- **Broadcast fallback**: If no channel specified, send to all
- **User ownership**: Each channel belongs to one user
- **Graceful degradation**: Handle unreachable channels gracefully

**Status files updated**:
- ✅ Design documentation created
- ✅ API endpoints defined
- ✅ Database models prepared
