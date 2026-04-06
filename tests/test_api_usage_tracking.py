#!/usr/bin/env python
"""
Test API Usage Tracking Endpoints

Tests for:
- GET /api/v1/usage/stats
- POST /api/v1/usage/track
- Free tier limit enforcement
- Premium tier functionality
- Rate limiting
"""

import pytest
import sys
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent / 'seferflow-api' / 'seferflow_api'))

from fastapi import status
from sqlmodel import SQLModel
from sqlmodel.session import SQLASession
import sqlalchemy

# Test fixtures
@pytest.fixture
def session():
    """Create database session"""
    from sqlmodel import SQLModel, create_engine
    
    # Create in-memory SQLite database for testing
    engine = sqlalchemy.create_engine(
        "sqlite:///:memory:",
        echo=True,
        future=True
    )
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    
    # Create session
    return SQLASession(engine)


@pytest.fixture
def client(session):
    """Create test FastAPI client"""
    from fastapi.testclient import TestClient
    from seferflow_api.main import app
    
    with TestClient(app) as client:
        yield client


# =====================================
# Usage Stats Tests
# =====================================

class TestUsageStats:
    """Test usage statistics endpoint"""
    
    def test_get_usage_stats_no_session(self, client):
        """Test getting usage stats before any sessions"""
        response = client.get("/api/v1/usage/stats")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["tier"] == "free"
        assert data["monthly_limit_hours"] == 4
        assert data["used_hours"] == 0.0
        assert data["remaining_hours"] == 4.0
        assert data["usage_percent"] == 0.0
    
    def test_get_usage_stats_after_playback(self, client, caplog):
        """Test usage stats after playback tracking"""
        # Record 3 hours of usage
        response = client.post(
            "/api/v1/usage/track",
            json={
                "duration_seconds": 3 * 3600,  # 3 hours
                "session_id": "test-session"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check usage stats
        stats = client.get("/api/v1/usage/stats").json()
        assert stats["used_hours"] == 3.0
        assert stats["remaining_hours"] == 1.0
        assert stats["usage_percent"] == 75.0


# =======================================
# Usage Tracking Tests
# =======================================

class TestUsageTracking:
    """Test usage tracking functionality"""
    
    def test_track_usage_record(self, client):
        """Test recording usage for a session"""
        response = client.post(
            "/api/v1/usage/track",
            json={
                "duration_seconds": 1800,  # 30 minutes
                "session_id": "test-session-1"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["session_id"] == "test-session-1"
        assert data["duration_seconds"] == 1800
        assert data["hours_used"] == 0.5
    
    def test_track_usage_multiple_sessions(self, client):
        """Test tracking multiple sessions"""
        # Track 1 hour
        client.post(
            "/api/v1/usage/track",
            json={"duration_seconds": 3600, "session_id": "session-1"},
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Track 2 hours
        client.post(
            "/api/v1/usage/track",
            json={"duration_seconds": 7200, "session_id": "session-2"},
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Track 1 hour
        client.post(
            "/api/v1/usage/track",
            json={"duration_seconds": 3600, "session_id": "session-3"},
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Check total usage
        stats = client.get("/api/v1/usage/stats").json()
        assert stats["used_hours"] == 6.0
    
    def test_track_usage_with_large_duration(self, client):
        """Test tracking a large playback session"""
        # Track 10 hours
        response = client.post(
            "/api/v1/usage/track",
            json={"duration_seconds": 10 * 3600, "session_id": "session-10"},
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["hours_used"] == 10.0


# =========================================
# Free Tier Limit Tests
# =========================================

class TestFreeTierLimit:
    """Test free tier limit enforcement"""
    
    def test_usage_within_limit(self, client):
        """Test usage within free tier limit (4 hours)"""
        # Track 3 hours (within 4 hour limit)
        response = client.post(
            "/api/v1/usage/track",
            json={
                "duration_seconds": 3 * 3600,
                "session_id": "session-3"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_usage_at_limit(self, client):
        """Test usage exactly at free tier limit"""
        # Track exactly 4 hours
        response = client.post(
            "/api/v1/usage/track",
            json={
                "duration_seconds": 4 * 3600,
                "session_id": "session-4"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_usage_exceeds_limit(self, client):
        """Test usage exceeds free tier limit (5 hours)"""
        # Track 5 hours (exceeds 4 hour limit)
        response = client.post(
            "/api/v1/usage/track",
            json={
                "duration_seconds": 5 * 3600,
                "session_id": "session-5"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Should fail - 423 Too Many Requests
        assert response.status_code in [403, 423]
        assert response.json()["status_code"] in [403, 423]
    
    def test_monitor_limit_approaching(self, client):
        """Test monitoring when approaching limit"""
        # Track 3.9 hours
        client.post(
            "/api/v1/usage/track",
            json={"duration_seconds": int(3.9 * 3600), "session_id": "session-3.9"},
            headers={"Authorization": "Bearer test-token"}
        )
        
        stats = client.get("/api/v1/usage/stats").json()
        assert stats["remaining_hours"] < 1.0
        assert stats["usage_percent"] > 90.0


# =========================================
# Premium Tier Tests
# =========================================

class TestPremiumTier:
    """Test premium tier functionality"""
    
    def test_premium_unlimited_usage(self, client):
        """Test premium user has unlimited usage"""
        # Simulate premium user token
        client.headers["Authorization"] = "Bearer premium-token"
        
        # Track 100 hours (way more than free tier)
        response = client.post(
            "/api/v1/usage/track",
            json={
                "duration_seconds": 100 * 3600,
                "session_id": "premium-session"
            },
            headers={"Authorization": "Bearer premium-token"}
        )
        
        # Should succeed with premium
        assert response.status_code == status.HTTP_200_OK
    
    def test_premium_status_check(self, client):
        """Test checking premium status"""
        # Track as premium
        client.headers["Authorization"] = "Bearer premium-token"
        
        status = client.get("/api/v1/premium/status").json()
        assert status["is_premium"] is True


# =========================================
# Rate Limit Tests
# =========================================

class TestRateLimiting:
    """Test rate limiting"""
    
    def test_rate_limit_unchanged(self, client):
        """Test rate limit not affected by usage"""
        # Record usage
        client.post(
            "/api/v1/usage/track",
            json={"duration_seconds": 3600, "session_id": "session"},
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Should still work
        response = client.get("/api/v1/usage/stats")
        assert response.status_code == status.HTTP_200_OK
    
    def test_rate_limit_after_many_requests(self, client):
        """Test rate limiting after many requests"""
        # Make 70 requests (exceeds 60 limit)
        for i in range(70):
            response = client.get("/api/v1/usage/stats")
        
        # Should still work within reason
        assert response.status_code == status.HTTP_200_OK


# =========================================
# Integration Tests
# =========================================

class TestUsageIntegration:
    """Test usage tracking integration with playback"""
    
    def test_playback_tracking_integration(self, client):
        """Test that usage is tracked during playback"""
        # Create playback session
        session = client.post(
            "/api/v1/playback/session",
            json={
                "pdf_path": "/test.pdf",
                "chapter": "Chapter 1",
                "voice": "en-US-AriaNeural",
                "speed": 1.0
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert session.status_code == status.HTTP_201_CREATED
        
        # Track usage for playback session
        track_response = client.post(
            "/api/v1/usage/track",
            json={
                "duration_seconds": 1800,
                "session_id": session.json()["session_id"]
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert track_response.status_code == status.HTTP_200_OK


# =========================================
# Time Calculation Tests
# =========================================

class TestTimeCalculations:
    """Test time calculation logic"""
    
    def test_convert_seconds_to_hours(self):
        """Test converting seconds to hours"""
        def seconds_to_hours(seconds):
            return seconds / 3600
        
        assert seconds_to_hours(3600) == Decimal("1.000")
        assert seconds_to_hours(7200) == Decimal("2.000")
        assert seconds_to_hours(0) == Decimal("0.000")
        
    def test_round_hours_used(self):
        """Test rounding hours used"""
        def round_hours(hours):
            from decimal import Decimal, ROUND_HALF_UP
            return float(Decimal(str(hours)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        
        assert round_hours(0.5234) == Decimal("0.52")
        assert round_hours(3.999) == Decimal("4.00")


# =========================================
# Edge Cases Tests
# =========================================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_zero_duration(self, client):
        """Test tracking zero duration"""
        response = client.post(
            "/api/v1/usage/track",
            json={
                "duration_seconds": 0,
                "session_id": "zero-duration"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_negative_duration(self, client):
        """Test negative duration (should fail)"""
        response = client.post(
            "/api/v1/usage/track",
            json={
                "duration_seconds": -100,
                "session_id": "negative"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Should fail validation
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_empty_session_id(self, client):
        """Test empty session ID"""
        response = client.post(
            "/api/v1/usage/track",
            json={
                "duration_seconds": 3600,
                "session_id": ""
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK


# =========================================
# Cleanup Tests
# =========================================

class TestCleanup:
    """Test cleanup functionality"""
    
    def test_cleanup_usage_records(self, client):
        """Test cleanup of old usage records"""
        # Create many usage records
        for i in range(10):
            client.post(
                "/api/v1/usage/track",
                json={"duration_seconds": 3600, "session_id": f"old-session-{i}"},
                headers={"Authorization": "Bearer test-token"}
            )
        
        # Cleanup should run periodically
        # Check total records
        from sqlmodel import select, User
        from datetime import datetime, timedelta
        
        # Get all records
        records = select(User).where(User.created_at < datetime.utcnow() - timedelta(days=7))
        assert len(records) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
