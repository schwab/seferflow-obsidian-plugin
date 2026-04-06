#!/usr/bin/env python3
"""
Channel Models - Device fingerprinting and persistent channel assignment
"""

from sqlmodel import SQLModel, Field
from datetime import datetime
from enum import Enum
import hashlib
from typing import Optional, List


class ChannelType(str, Enum):
    """Types of playback clients"""
    OBSIDIAN = "obsidian"
    TUI = "tui"
    WEB = "web"
    MOBILE = "mobile"
    CLI = "cli"


class StatusType(str, Enum):
    """Channel status states"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"


# Device fingerprint fields for identifying the same player across sessions
DEVICE_FINGERPRINT_FIELDS = [
    "host_id", 
    "device_id", 
    "version", 
    "client_type", 
    "user_agent", 
    "ip_address",
    "os",
    "browser"
]

def create_device_fingerprint(**kwargs) -> str:
    """
    Create a persistent device fingerprint from fingerprint fields.
    
    The fingerprint is created by hashing all provided fingerprint fields.
    This allows us to identify the same player across sessions.
    
    Args:
        **kwargs: Any combination of device fingerprint fields
        
    Returns:
        Short, consistent fingerprint string
    """
    # Only use fields that were provided
    fingerprint_data = ",".join([f'{key}={value}' for key, value in kwargs.items() if value])
    
    # Hash the fingerprint data
    hash_obj = hashlib.sha256(fingerprint_data.encode())
    return hash_obj.hexdigest()[:16]


class Channel(SQLModel, table=True):
    """
    Playback channel model
    
    A channel represents one playback client instance for a user.
    Each channel has a persistent ID that never changes.
    
    Channels are identified by:
    - User ID + Device Fingerprint + Client Type
    
    This allows the same player to be identified across sessions
    and reuse their previous channel ID.
    """
    
    __tablename__ = "channels"
    
    # Channel identity (immutable)
    id: Optional[str] = Field(
        primary_key=True,
        description="Persistent channel ID"
    )
    user_id: str = Field(
        foreign_key="users.id",
        index=True,
        description="Owner user ID"
    )
    fingerprint: str = Field(
        index=True,
        description="Device fingerprint for identification"
    )
    client_type: str = Field(
        default="web",
        description="Client type (obsidian, tui, web, mobile, cli)"
    )
    type: ChannelType = Field(
        default=ChannelType.WEB,
        description="Channel type"
    )
    
    # Metadata
    name: str = Field(
        default="",
        max_length=100,
        description="Display name for this channel"
    )
    description: str = Field(
        sa_column_kwargs={"default": ""},
        max_length=500,
        description="User-facing description"
    )
    
    # Technical details
    host_id: Optional[str] = Field(
        sa_column_kwargs={"default": None},
        description="Hosting system identifier"
    )
    device_id: Optional[str] = Field(
        sa_column_kwargs={"default": None},
        description="Device identifier"
    )
    version: str = Field(
        default="unknown",
        max_length=50,
        description="Client library version"
    )
    user_agent: Optional[str] = Field(
        sa_column_kwargs={"default": None},
        max_length=255,
        description="User agent string"
    )
    ip_address: Optional[str] = Field(
        sa_column_kwargs={"default": None},
        description="Client IP address"
    )
    os: Optional[str] = Field(
        sa_column_kwargs={"default": None},
        description="Operating system"
    )
    browser: Optional[str] = Field(
        sa_column_kwargs={"default": None},
        description="Browser/client"
    )
    
    # Status tracking
    is_active: bool = Field(
        default=True,
        description="Is channel currently active/connected"
    )
    last_seen: datetime = Field(
        default_factory=datetime.utcnow,
        index=True,
        description="Last heartbeat from channel"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Channel creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last updated timestamp"
    )
    
    # Usage tracking
    playback_hours_total: float = Field(
        default=0.0,
        description="Total playback hours on this channel"
    )
    total_interruptions: int = Field(
        default=0,
        description="Number of MCP interruptions received"
    )
    
    # Configuration
    speed: float = Field(
        default=1.0,
        description="Default playback speed"
    )
    voice: str = Field(
        default="en-US-AriaNeural",
        description="Default voice for channel"
    )
    channel_name: Optional[str] = Field(
        default="Channel",
        description="Channel display name"
    )
    
    @property
    def fingerprint_fields_hash(self) -> str:
        """Hash of all fingerprint fields for quick lookup"""
        return create_device_fingerprint(**self)
    
    @property
    def is_online(self) -> bool:
        """
        Check if channel has been active recently
        
        A channel is considered online if it's marked active
        and has been seen within the last 5 minutes.
        """
        return self.is_active and (datetime.utcnow() - self.last_seen).seconds < 300
    
    @property
    def time_since_last_seen(self) -> int:
        """Get seconds since last heartbeat"""
        return (datetime.utcnow() - self.last_seen).seconds
    
    def __repr__(self):
        online = "🟢" if self.is_online else "🔴"
        return (
            f"<Channel({self.id}: {self.name} - {self.type.value} | "
            f"{online}: {self.fingerprint[:8]}...)"
        )
    
    def __eq__(self, other):
        """Compare channels by fingerprint, not just ID."""
        if other is None:
            return False
        return self.fingerprint == other.fingerprint
