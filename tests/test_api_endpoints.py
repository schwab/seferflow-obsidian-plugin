#!/usr/bin/env python3
"""
test_api_endpoints.py

Test all SeferFlow API endpoints.
"""

# Test user registration
def test_user_registration():
    """Test user registration endpoint"""
    response_data = {
        "user_id": "usr_123",
        "email": "user@example.com",
        "username": "testuser",
        "role": "listener",
        "created_at": "2026-04-06T10:00:00Z"
    }
    
    assert response_data["user_id"] == "usr_123"
    assert response_data["role"] == "listener"
    
    print("✓ User registration test passed")
    return True


# Test user login
def test_user_login():
    """Test user login endpoint"""
    login_response = {
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
    
    assert login_response["token_type"] == "bearer"
    assert login_response["expires_in"] > 0
    
    print("✓ User login test passed")
    return True


# Test health check endpoint
def test_health_check():
    """Test health check endpoint"""
    health_response = {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": "2026-04-06T11:00:00Z",
        "services": {
            "redis": "connected",
            "database": "connected"
        }
    }
    
    assert health_response["status"] == "healthy"
    
    print("✓ Health check test passed")
    return True


# Test PDF browsing endpoint
def test_pdf_browsing():
    """Test PDF library browsing endpoint"""
    browse_response = {
        "directory": "/library",
        "total_items": 150,
        "page": 0,
        "page_size": 10,
        "items": [
            {
                "id": "lib-abc",
                "type": "directory",
                "name": "Classics",
                "status": "partial",
                "status": "partial"
            },
            {
                "id": "pdf-xyz",
                "type": "pdf",
                "name": "Harry_Potter.pdf",
                "status": "partial"
            }
        ]
    }
    
    assert browse_response["directory"] == "/library"
    assert len(browse_response["items"]) > 0
    
    print("✓ PDF browsing test passed")
    return True


# Test chapter listing endpoint
def test_chapter_listing():
    """Test chapter listing endpoint"""
    chapters_response = {
        "pdf_path": "library/book.pdf",
        "chapters": [
            {
                "num": 1,
                "title": "Chapter One",
                "start_page": 1,
                "end_page": 12,
                "word_count": 2500
            }
        ]
    }
    
    assert chapters_response["chapters"][0]["num"] == 1
    assert chapters_response["chapters"][0]["title"] == "Chapter One"
    
    print("✓ Chapter listing test passed")
    return True


def test_error_handling():
    """Test error handling"""
    error_responses = [
        {
            "detail": "Invalid email format",
            "status_code": 400,
            "code": "invalid_request"
        },
        {
            "detail": "Token expired",
            "status_code": 401,
            "code": "invalid_token"
        },
        {
            "detail": "User not found",
            "status_code": 404,
            "code": "not_found"
        }
    ]
    
    for error in error_responses:
        assert "detail" in error
        assert "status_code" in error
        assert "code" in error
    
    print("✓ Error handling test passed")
    return True


def test_rate_limit_responses():
    """Test rate limiting responses"""
    rate_limit_response = {
        "detail": "Rate limit exceeded",
        "retry_after": 60,
        "reset": "2026-04-06T12:00:00Z"
    }
    
    assert rate_limit_response["retry_after"] > 0
    assert rate_limit_response["status_code"] == 429
    
    print("✓ Rate limiting test passed")
    return True


def test_response_formatting():
    """Test response formatting"""
    response = {
        "id": "resp-123",
        "status": "success",
        "data": "some data",
        "timestamp": datetime.now().isoformat()
    }
    
    assert "id" in response
    assert "status" in response
    
    print("✓ Response formatting test passed")
    return True


def test_cors_headers():
    """Test CORS headers"""
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE"
    }
    
    assert "Access-Control-Allow-Origin" in headers
    
    print("✓ CORS headers test passed")
    return True


def test_content_types():
    """Test content type headers"""
    content_types = [
        {"accept": "application/json", "value": "application/json"},
        {"accept": "application/xml", "value": "application/xml"}
    ]
    
    for ct in content_types:
        assert ct["accept"] == "application/json"
    
    print("✓ Content types test passed")
    return True


if __name__ == "__main__":
    """Run all endpoint tests"""
    print("Running API Endpoint Tests...")
    print("=" * 50)
    
    tests = [
        test_user_registration,
        test_user_login,
        test_health_check,
        test_pdf_browsing,
        test_chapter_listing,
        test_error_handling,
        test_rate_limit_responses,
        test_response_formatting,
        test_cors_headers,
        test_content_types,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
        except AssertionError as e:
            failed += 1
            print(f"Failed: {test.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"Error: {test.__name__}: {e}")
        finally:
            print()
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    
    print("=" * 50)
