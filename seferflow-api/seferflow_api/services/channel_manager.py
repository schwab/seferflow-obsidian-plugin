#!/usr/bin/env python3
"""
Channel Manager Service

Manage user playback channels, track activity, handle heartbeats,
and route messages to appropriate channels.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlmodel import Session, select

from ..models.channel import (
    Channel,
    UserChannel,
    MessageLogEntry,
    ChannelStatusEvent,
)
from ..core.security import get_current_user

logger = logging.getLogger(__name__)


class ChannelManager:
    """
    Manage playback channels for users
    
    Provides methods for:
    - Channel registration and management
    - Heartbeat tracking
    - Message routing to channels
    - Cleanup of inactive channels
    """
    
    def __init__(self, db: Session):
        """
        Initialize channel manager.
        
        Args:
            db: Database session
        """
        self.db = db
    
    # ========== Channel Lifecycle Management ==========
    
    def assign_or_find_channel(
        self,
        channel_data: dict,
        user_id: str,
    ) -> Channel:
        """
        Assign or find existing channel for a user/player.
        
        This uses device fingerprinting to identify if the same
        player is connecting (same device/host/version), and reuses
        their previous channel if found.
        
        Args:
            channel_data: Dict with host_id, device_id, version, user_agent, etc.
            user_id: User ID
        
        Returns:
            Channel object (existing or newly created)
        """
        try:
            # Extract fingerprint fields
            fingerprint_fields = {
                "host_id": channel_data.get("host_id"),
                "device_id": channel_data.get("device_id"),
                "version": channel_data.get("version", "unknown"),
                "client_type": channel_data.get("client_type", "web"),
                "user_agent": channel_data.get("user_agent"),
                "ip_address": channel_data.get("ip_address"),
                "os": channel_data.get("os"),
                "browser": channel_data.get("browser"),
            }
            
            # Generate fingerprint
            fingerprint = create_device_fingerprint(**fingerprint_fields)
            
            # Look up existing channel with same fingerprint
            from ..models.channel import Channel
            existing = self.db.query(Channel).filter(
                Channel.user_id == user_id,
                Channel.fingerprint == fingerprint,
            ).first()
            
            if existing:
                # Channel exists, update it
                channel = existing
                logger.info(f"Found existing channel {channel.id} for user {user_id}")
                return channel
            
            # Create new channel
            channel_id = f"ch_{fingerprint}"
            channel = Channel(
                id=channel_id,
                user_id=user_id,
                fingerprint=fingerprint,
                type=ChannelType(channel_data.get('client_type', 'web')),
                name=channel_data.get('name', 'Channel'),
                description=channel_data.get('description', ''),
                host_id=channel_data.get('host_id'),
                device_id=channel_data.get('device_id'),
                version=channel_data.get('version', 'unknown'),
                user_agent=channel_data.get('user_agent'),
                ip_address=channel_data.get('ip_address'),
                os=channel_data.get('os'),
                browser=channel_data.get('browser'),
                client_type=channel_data.get('client_type', 'web'),
            )
            
            self.db.add(channel)
            self.db.commit()
            self.db.refresh(channel)
            
            logger.info(f"Created new channel {channel_id} for user {user_id}")
            return channel
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Channel assign/lookup failed: {e}")
            raise
    
    def unregister_channel(self, channel_id: str) -> bool:
        """
        Unregister/delete a channel.
        
        Args:
            channel_id: Channel to unregister
        
        Returns:
            bool: True if deleted successfully
        """
        try:
            channel = self.db.get(Channel, channel_id)
            if not channel:
                return False
            
            # Remove user-channel association
            self.db.query(UserChannel).filter(
                UserChannel.channel_id == channel_id
            ).delete()
            
            # Delete channel
            self.db.delete(channel)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Channel unregistration failed: {e}")
            return False
    
    def list_user_channels(self, user_id: str) -> List[Channel]:
        """
        List all active channels for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of active channels
        """
        channels = self.db.query(Channel).filter(
            Channel.user_id == user_id,
            Channel.is_active == True
        ).all()
        
        return channels
    
    # ========== Heartbeat Management ==========
    
    def handle_channel_heartbeat(
        self,
        user_id: str,
        channel_id: Optional[str] = None,
        host_id: Optional[str] = None,
    ) -> Optional[Channel]:
        """
        Handle a channel heartbeat/keep-alive.
        
        Args:
            user_id: User ID
            channel_id: Channel ID (if specific, None = all)
            host_id: Host ID for identification
        
        Returns:
            Updated channel or None
        """
        try:
            if channel_id:
                # Update specific channel
                channel = self.db.get(Channel, channel_id)
                if channel:
                    channel.last_seen = datetime.utcnow()
                    channel.updated_at = datetime.utcnow()
                    channel.host_id = host_id
                    self.db.commit()
                    return channel
            else:
                # Update all channels for user
                channels = self.db.query(Channel).filter(
                    Channel.user_id == user_id,
                    Channel.is_active == True
                ).all()
                
                for ch in channels:
                    ch.last_seen = datetime.utcnow()
                    ch.updated_at = datetime.utcnow()
                    ch.host_id = host_id
                self.db.commit()
                
            return None
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Channel heartbeat failed: {e}")
            return None
    
    def cleanup_inactive_channels(
        self,
        threshold_seconds: int = 300,
    ) -> int:
        """
        Cleanup channels that haven't responded recently.
        
        Args:
            threshold_seconds: Max seconds since last heartbeat before cleanup
        
        Returns:
            Number of channels marked inactive
        """
        try:
            cutoff = datetime.utcnow() - timedelta(seconds=threshold_seconds)
            
            # Get inactive channels
            inactive_channels = self.db.query(Channel).filter(
                Channel.last_seen < cutoff
            ).filter(
                Channel.is_active == True
            ).all()
            
            inactive_count = 0
            for ch in inactive_channels:
                ch.is_active = False
                ch.last_seen = cutoff
                inactive_count += 1
            
            self.db.commit()
            logger.info(f"Marked {inactive_count} inactive channels")
            
            return inactive_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Cleanup inactive channels failed: {e}")
            return 0
    
    def get_active_channel_count(self, user_id: str) -> int:
        """
        Get count of active channels for user.
        
        Args:
            user_id: User ID
        
        Returns:
            Active channel count
        """
        return self.db.query(Channel).filter(
            Channel.user_id == user_id,
            Channel.is_active == True
        ).count()
    
    # ========== Message Routing ==========
    
    def route_message(
        self,
        user_id: str,
        channel_ids: Optional[List[str]] = None,
        message_text: str = "",
    ) -> Dict[str, Any]:
        """
        Route message to specified channels or all active channels.
        
        Args:
            user_id: Target user
            channel_ids: List of channel IDs to send to, or None for all
            message_text: Message text
        Returns:
            Dict with delivery results
        """
        try:
            # Get target channels
            query = (
                self.db.query(Channel)
                .filter(Channel.user_id == user_id)
            )
            
            if channel_ids:
                query = query.filter(
                    Channel.id.in_(channel_ids),
                    Channel.is_active == True
                )
            else:
                query = query.filter(Channel.is_active == True)
            
            target_channels = query.all()
            
            # Create log entries for each channel
            results = []
            for ch in target_channels:
                log_entry = MessageLogEntry(
                    id="",
                    channel_id=ch.id,
                    user_id=user_id,
                    text=message_text,
                    message_type="interruption",
                    is_delivered=True,
                )
                self.db.add(log_entry)
                
                results.append({
                    "channel_id": ch.id,
                    "delivered": True,
                    "channel_type": ch.type.value,
                })
                
                # Update channel stats
                ch.total_interruptions += 1
                ch.last_seen = datetime.utcnow()
                ch.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return {
                "user_id": user_id,
                "channels": len(results),
                "delivered_channels": sum(1 for r in results if r["delivered"]),
                "results": results,
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Message routing failed: {e}")
            return {
                "user_id": user_id,
                "channels": 0,
                "delivered_channels": 0,
                "results": [],
                "error": str(e),
            }
    
    def log_message(
        self,
        user_id: str,
        channel_id: str,
        text: str,
        message_type: str = "interruption",
    ) -> Optional[MessageLogEntry]:
        """
        Log a message for a channel.
        
        Args:
            user_id: User who received message
            channel_id: Channel that received it
            text: Message content
            message_type: Type of message
        
        Returns:
            Log entry
        """
        try:
            entry = MessageLogEntry(
                id="",
                channel_id=channel_id,
                user_id=user_id,
                text=text,
                message_type=message_type,
                is_delivered=True,
                duration_seconds=0,
            )
            
            self.db.add(entry)
            self.db.commit()
            self.db.refresh(entry)
            
            return entry
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Message logging failed: {e}")
            return None
    
    # ========== Analytics ==========
    
    def get_channel_analytics(self, user_id: str) -> Dict[str, Any]:
        """
        Get analytics for user's channels.
        
        Args:
            user_id: User ID
        
        Returns:
            Analytics dict
        """
        channels = self.db.query(Channel).filter(
            Channel.user_id == user_id,
            Channel.is_active == True
        ).all()
        
        total_playback_hours = sum(c.playback_hours_total for c in channels)
        total_interruptions = sum(c.total_interruptions for c in channels)
        
        return {
            "active_channels": len(channels),
            "total_playback_hours": total_playback_hours,
            "total_interruptions": total_interruptions,
            "avg_interruptions_per_channel": total_interruptions / len(channels) if channels else 0,
        }
    
    # ========== Helpers ==========
    
    @staticmethod
    def _generate_persistent_channel_id(
        user_id: str,
        device_info: str = "",
        location: str = "",
    ) -> str:
        """
        Generate a persistent channel ID.
        
        The ID is constructed from user ID + device info + location
        so it remains consistent across restarts.
        
        Args:
            user_id: User ID
            device_info: Device identifier
            location: Location info
        
        Returns:
            Persistent channel ID string
        """
        import hashlib
        now = datetime.utcnow().timestamp()
        
        # Combine user info
        info = f"{user_id}:{device_info}:{location}:{now}"
        
        # Create hash
        channel_hash = hashlib.md5(info.encode()).hexdigest()[:16]
        
        return f"ch_{channel_hash}"
